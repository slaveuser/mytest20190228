README.txt
Install Dependencies:
	pip install reqirements.txt

N.B. Running rq on windows requires a Unix emaulator, e.g. Ubuntu

Start redis server:
	(Windows cmd) redis-server --service-start
	
Start Flask app:
	(Ubuntu emulator)
	workon csproject
	Dev:
		(from mnt/c/Users/.../csProject) python2.7 app.py
	Production:
		(from mnt/c/Users/.../csProject) gunicorn -w 4 -b 0.0.0.0:5000 manage:app --timeout 90
Start RQ worker:
	(Ubuntu emulator)
	workon csproject
	(from mnt/c/Users/.../csProject) rq worker default