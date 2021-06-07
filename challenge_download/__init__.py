import json
import os
import uuid
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

from flask import render_template, request, redirect, url_for, session
from werkzeug.exceptions import abort

from CTFd.api.v1.comments import get_comment_model
from CTFd.models import Challenges, Files, db
from CTFd.plugins import override_template
from CTFd.plugins.challenge_download.forms import ChallengeDownloadForm, ChallengeUploadForm
from CTFd.plugins.challenge_download.serializers import serialize, challenge_from_config
from CTFd.plugins.challenge_download.util import get_template_path
from CTFd.plugins.challenges import get_chal_class
from CTFd.schemas.challenges import ChallengeSchema
from CTFd.schemas.flags import FlagSchema
from CTFd.schemas.hints import HintSchema
from CTFd.schemas.tags import TagSchema
from CTFd.utils.decorators import admins_only
from CTFd.utils.uploads import delete_file, upload_file


@admins_only
def challenge_download_list():
    challenges = Challenges.query.all()
    form = ChallengeDownloadForm()
    return render_template('challenge_download_list.html', challenges=challenges, form=form)


@admins_only
def challenge_download_challenge():
    try:
        challenge_id = int(request.form['challenge_id'])
        action = request.form['action']
    except (KeyError, AttributeError, TypeError):
        return abort(400)

    challenge = Challenges.query.get(challenge_id)
    # print(f'{challenge_id}, {action}, {challenge}')

    if not challenge:
        return abort(404)

    if action == 'download':
        uploads_folder = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'uploads')
        challenge_json = serialize(challenge)
        files_paths = [os.path.join(uploads_folder, x.location) for x in challenge.files]
        file_name = f'{challenge.name}.zip'
        folder_name = uuid.uuid4().hex
        os.makedirs(os.path.join(uploads_folder, folder_name))

        archive = BytesIO()
        with ZipFile(archive, 'w', ZIP_DEFLATED, False) as z:
            z.writestr('challenge.json', json.dumps(challenge_json))
            for file_path in files_paths:
                z.write(file_path, os.path.join('files', os.path.basename(file_path)))

        location = f'{folder_name}/{file_name}'
        with open(os.path.join(uploads_folder, location), 'wb+') as f:
            f.write(archive.getvalue())
        archive.close()

        previous_file = Files.query.filter(Files.location.contains(file_name)).first()
        if previous_file:
            delete_file(previous_file.id)

        file = Files(type="standard", location=location)
        db.session.add(file)

        db.session.commit()
        db.session.close()
        return redirect(url_for("views.files", path=location))
    else:
        return abort(404)


@admins_only
def challenge_upload():
    if request.method == 'GET':
        form = ChallengeUploadForm()
        return render_template('challenge_upload.html', form=form)
    else:
        for challenge_zip in request.files.getlist('challenge_zips'):
            with ZipFile(challenge_zip) as z:
                challenge_config = json.loads(z.read('challenge.json'))
                file_names = [x for x in z.namelist() if x.startswith('files')]

                files = []
                for file_name in file_names:
                    file_obj = BytesIO(z.read(file_name))
                    file_obj.filename = file_name.split('/')[-1]
                    files.append(file_obj)

            schema = ChallengeSchema()
            challenge_data = {k: v for k, v in challenge_config.items() if type(v) not in (dict, list)}
            response = schema.load(challenge_data)
            if response.errors:
                return abort(400)

            challenge_class = get_chal_class(challenge_data["type"])
            challenge = challenge_class.challenge_model(**challenge_data)
            db.session.add(challenge)
            db.session.commit()

            for file_obj in files:
                upload_file(file=file_obj, challenge_id=challenge.id, type='challenge')

            flags_data = challenge_config.get('flags') or []
            for flag_data in flags_data:
                flag_data['challenge_id'] = challenge.id
                schema = FlagSchema()
                response = schema.load(flag_data, session=db.session)
                db.session.add(response.data)

            hints_data = challenge_config.get('hints') or []
            for hint_data in hints_data:
                hint_data['challenge_id'] = challenge.id
                schema = HintSchema(view="admin")
                response = schema.load(hint_data, session=db.session)
                db.session.add(response.data)

            comments_data = challenge_config.get('comments') or []
            for comment_data in comments_data:
                comment_data['challenge_id'] = challenge.id
                comment_data['author_id'] = session["id"]
                CommentModel = get_comment_model(data=comment_data)
                comment = CommentModel(**comment_data)
                db.session.add(comment)

            tags_data = challenge_config.get('tags') or []
            for tag_data in tags_data:
                tag_data['challenge_id'] = challenge.id
                schema = TagSchema()
                response = schema.load(tag_data, session=db.session)
                # print(f'{response.data=}')
                db.session.add(response.data)
            db.session.commit()
            db.session.close()

        return redirect(url_for('admin.challenges_listing'))



def load(app):
    override_template('challenge_download_list.html', open(get_template_path('challenge_download_list.html')).read())
    override_template('challenge_upload.html', open(get_template_path('challenge_upload.html')).read())

    app.route('/admin/challenge_upload', methods=['GET', 'POST'])(challenge_upload)
    app.route('/admin/challenge_download')(challenge_download_list)
    app.route('/admin/challenge_download/challenge', methods=['POST'])(challenge_download_challenge)
