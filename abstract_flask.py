import json
import random
from glob import iglob

from werkzeug.utils import redirect

per_page = 27

def index():
    cards = []
    for i, file in enumerate(sorted(iglob('cache/idx/abs/*.json'), reverse=True)):
        if i > 100:
            break
        print('file:', file)
        with open(file) as f:
            cards.append(json.loads(f.read()))
    print('index cards', cards)
    return cards


def page(ref):
    json.loads(f'cache/sums/pdfs/pds_{ref}.json')


from flask import Flask, Response, request
from flask import render_template

app = Flask(__name__)

from itertools import groupby


# define a fuction for key
def themes_key(k):
    return k['theme']


@app.route('/')
def home():
    # themes = {k[v] for k, v in groupby(index(), key=lambda x: x['theme'])}
    # sort INFO data by 'company' key.
    themes = dict()
    index_cards = sorted(index(), key=themes_key)
    for theme, cards in groupby(index_cards, themes_key):
        print('theme', theme)
        card_list = list(cards)[0:3]
        random.shuffle(card_list)
        print('card list', card_list)
        themes[theme] = card_list
    print('themes', themes)
    return render_template('index.html', themes=themes)

@app.route('/spot/<ref>')
def page(ref):
    try:
        float(ref)
    except ValueError:
        return ''
    try:
        with open(f"cache/sums/pdfs/_pdf_{ref}.json") as f:
            article = json.loads(f.read())
    except Exception:
        return ""
    article['theme'] = article.get("theme", '')
    return render_template('page.html', ref=ref, article=article, paragraphs=article['paragraphs'])


def show_binary(image, path='html/images/'):
    image = image.replace('..', '')
    try:
        with open(path + image, 'rb') as f:
            img = f.read()
    except Exception:
        return ''
    return img


@app.route('/theme/<theme>')
def theme(theme):
    page = request.args.get('page', default=1, type=int)
    print('page', page)
    spots = [abs for abs in index() if abs['theme'] == theme.replace('_', ' ')]
    spots = list(spots)[((page * per_page) - per_page) : (page * per_page)]
    if not spots:
        return redirect("/", code=302)
    return render_template(
        'theme.html',
        theme=theme,
        theme_title=theme.replace('_', ' '),
        spots=spots,
        page=page
    )


@app.route('/html/<folder>/<image>')
def show_image(folder, image):
    return show_binary(image, path=f'html/{folder}/')


@app.route('/html/<file>')
def show_file(file: str):
    binary = show_binary(file, path='html/')
    if file.endswith('.css'):
        return Response(binary, mimetype='text/css')
    if file.endswith('.js'):
        return Response(binary, mimetype='text/javascript')
    return binary


app.run(host='0.0.0.0', port=8000)
