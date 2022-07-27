set -x
# start server
python abstract_flask.py

# mirror contents
cd mirror
wget --mirror http://localhost:8000
cd -

# upload
cd mirror/localhost:8000
find . -exec curl --insecure -T {} 'https://traverse.depth.hu:2078/{}' --user "traverse@traverse.depth.hu:`cat password.txt`" \;
cd -
