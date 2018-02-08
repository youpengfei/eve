# -*- coding: UTF-8 -*-

from eve import app, db, route

if __name__ == '__main__':
    #db.create_all()
    app.run(debug=True, host='0.0.0.0')
