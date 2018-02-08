
from flask import render_template, Blueprint
from flask.ext.login import current_user, login_required

mod = Blueprint('ecs', __name__)

@mod.route('/list', methods=['GET', 'POST'])
@login_required
def show_ecs_list():
    return render_template('ecs_list.html')