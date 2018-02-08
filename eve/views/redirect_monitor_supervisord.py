
from flask import render_template, Blueprint
from flask.ext.login import current_user, login_required

mod = Blueprint('redirect_monitor_supervisord', __name__)

@mod.route('/list', methods=['GET', 'POST'])
@login_required
def monitor_list():
    return render_template('monitor_supervisord_list.html')