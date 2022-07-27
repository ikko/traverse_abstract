import datetime
import json
import os
import random
import re
import sys
import traceback

import argparse
import requests
from tqdm.auto import tqdm
from transformers import pipeline
from requests_html import HTMLSession
import fitz  # pymupdf

from abstract_utils import dirs

length = 100
summarization = pipeline("summarization", min_length=length)
session = HTMLSession()
for dir in dirs:
    os.makedirs(dir, exist_ok=True)


def summarize(original_text):
    max_token_nr = 1000
    model_default_token_target = 142
    model_default_min_length = 100
    tokens_nr = len(summarization.tokenizer(original_text)['input_ids'])
    print('tokens_nr', tokens_nr, end=' ')
    if len(original_text) <= length:
        return original_text
    summary_texts = []
    if tokens_nr > max_token_nr:
        sentences = original_text.split('. ')
        sentences = [s + '. ' for s in sentences]
        print('sentences_nr', len(sentences), end=' ')
        sentence_token_nrs = [len(summarization.tokenizer(sentence)['input_ids']) for sentence in sentences]
        while sentences:
            part_text = ''
            part_tokens_nr = 0
            for i in range(len(sentences)):
                # while parttext is short
                if part_tokens_nr + sentence_token_nrs[0] > max_token_nr:
                    break
                part_tokens_nr += sentence_token_nrs.pop(0)
                part_text += sentences.pop(0)
            print('.', end='')
            # print('summarizing, part_tokens_nr:', part_tokens_nr, 'sentences_left', len(sentences))
            if part_tokens_nr:
                half_token_nr = part_tokens_nr // 2
                target_length = max(model_default_min_length, min(half_token_nr, model_default_token_target))
                summary_texts.append(summarization(part_text, max_length=target_length)[0]['summary_text'])
            else:
                # if could not split to senteces
                print(f"sentence too big, splitting in half, part_tokens_nr is {part_tokens_nr}")
                sentence = sentences[0]
                sentence_length_half = len(sentence)//2
                first_half = sentence[:sentence_length_half]
                last_half = sentence[sentence_length_half:]
                sentences.pop(0)
                sentences.insert(0, last_half)
                sentences.insert(0, first_half)
                sentence_token_nrs = [len(summarization.tokenizer(sentence)['input_ids']) for sentence in sentences]
        sentence_token_nrs = [len(summarization.tokenizer(sentence)['input_ids']) for sentence in sentences]
        summary_text = '\n'.join(summary_texts)
    else:
        # print('original_text', original_text)
        summary_text = summarization(original_text)[0]['summary_text']

    summary_text = cleanup(summary_text)
    # print("Summary is:", summary_text)
    print(".")
    return summary_text


def cleanup(text):
    text = re.sub(r"- +", "", text)   # remove conca-   tenation
    text = text.replace('Our ', 'The ')
    text = text.replace('our ', 'the ')
    text = text.replace('We ', 'They ')
    text = text.replace('we ', 'they ')
    text = ''.join(['' if ord(c) == 160 else c for c in text])
    text = re.sub(r"\[[0-9,\, ]+\]", '', text)
    text = re.sub(r" +", " ", text)
    text = text.replace(' ..', '.').replace(' .', '.')
    text = text.replace(' ,,', ',').replace(' ,', ',')
    text = re.sub(r"Table [0-9]+: ", "", text)
    text = re.sub(r"Figure [0-9]+: ", "", text)
    text = text.replace("In , ", '')
    text = text.replace("in , ", '')
    text = text.replace('<br>', ' ')
    text = text.replace('<br/>', ' ')
    text = re.sub(r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*", "", text)
    return text


def first_image(pdf_file, pdf):
    doc = fitz.open(pdf_file)
    png_name = 'images/' + pdf.replace("/", "_") + '.png'
    png_disk_name = 'html/images/' + pdf.replace("/", "_") + '.png'
    found = False
    for i in range(len(doc)):
        for img in doc.get_page_images(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:  # this is GRAY or RGB
                try:
                    pix.save(png_disk_name)  # pix.save("p%s-%s.png" % (i, xref))
                except AttributeError as e:
                    logger(e, png_disk_name)
                    continue
            else:  # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                try:
                    pix1.save(png_disk_name)  # pix1.save("p%s-%s.png" % (i, xref))
                except AttributeError as e:
                    logger(e, png_disk_name)
                    continue

            found = True
            break
        if found:
            break
    if not found:
        print("no image found")
        return "abstract.png"
    print('image is:', png_name)
    return png_name



def openpage(link='/abs/2011.05519', theme='main'):
    r = session.get('https://arxiv.org' + link)
    print("=" * 80)
    print('link is', link)
    title = ''.join(r.html.find('h1.title.mathjax')[0].text.split('\n')[0].strip().split('.')[0].split('Title:')[1:])
    print("title is", title)
    abstract = ''.join(r.html.find('blockquote.abstract.mathjax')[0].text.strip().split('\n')[0].split('Abstract:')[1:])
    # print("abstract is", abstract)
    pdf = r.html.find('.download-pdf')[0].attrs['href']
    print('pdf is', pdf)
    response = requests.get('https://arxiv.org' + pdf)
    pdf_filename = 'pdfs/' + pdf.replace('/', '_') + '.pdf'
    open(pdf_filename, "wb").write(response.content)
    extract_pdf(pdf, title=title, theme=theme)
    image_name = first_image(pdf_filename, pdf)
    print('-' * 80)
    if len(abstract) > length:
        summary = summarize(abstract).replace(" .", ".")
    else:
        summary = abstract
    return title, summary, image_name

def extract_pdf(pdf, title='title', theme="main"):
    filename = pdf.replace("/", "_") + '.pdf'
    pdf_diskfile = 'pdfs/' + filename
    html_name = f'sums/{filename}'.replace('_pdf_', '_sum_').replace('.pdf', '.html')
    print(html_name)
    summarize_pdf(pdf_file=pdf_diskfile, html_file=html_name, title=title, theme=theme)
    print(html_name)
    return html_name

header = '<html><head><link rel="stylesheet" href="style.css"><script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.0.1/js/bootstrap.min.js" integrity="sha512-EKWWs1ZcA2ZY9lbLISPz8aGR2+L7JVYqBAYTq5AXgBkSjRSuQEGqWx8R1zAX16KdXPaCjOCaKE8MCpU0wcHlHA==" crossorigin="anonymous" referrerpolicy="no-referrer"></script></head>\n'


def summarize_pdf(pdf_file, html_file, title, theme):
    doc = fitz.open(pdf_file)
    png_images = retrieve_images(doc, html_file)
    png1 = png_images[0] if len(png_images) >= 1 else 'abstract.png'
    png2 = png_images[1] if len(png_images) >= 2 else 'abstract.png'

    page_summaries = [p.strip() for p in retreive_pages(doc)]
    page1 = page_summaries[0] if len(page_summaries) >= 1 else ''
    page2 = page_summaries[1] if len(page_summaries) >= 2 else ''

    # with open('html/' + html_file, 'w') as f:
    #     f.write(header)
    #     f.write('<h1>abstract</h1>\n')
    #     f.write(f'<h3>{title}</h3>\n')
    #     f.write(f'<h3>{title}</h3>\n')
    #     f.write(f'<img src="{png1}">\n')
    #     f.write(f'<p class="text"> {page1} </p>\n')
    #     f.write(f'<img src="{png2}">\n')
    #     f.write(f'<p class="text"> {page2} </p>\n')
    #     for page in page_summaries[3:]:
    #         f.write(f'<p class="text"> {page} </p>\n')
    with open("cache/sums/" + pdf_file[:-4] + '.json', 'w') as f:
        f.write(json.dumps(dict(theme=theme, title=title, png1=png1, png2=png2, page1=page1, page2=page2, paragraphs=page_summaries)))


def retreive_pages(doc):
    page_summaries = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        text = page.get_text()
        if 'References' in text:
            break
        try:
            page_summaries.append(summarize(text))
        except Exception as e:
            logger(e, text)
    return page_summaries


def logger(e, text):
    with open('logs/abstract.log', 'a') as f:
        f.write(json.dumps(dict(at=datetime.datetime.now().isoformat(), exception=repr(e), text=text)))
        f.write('\n')
        traceback.print_stack(file=f)
        f.write('-' * 80 + '\n')
        f.write(repr(e))


def retrieve_images(doc, html_file):
    png1_name = html_file + '.1.png'
    png2_name = html_file + '.2.png'
    png_found = []
    for i in range(len(doc)):
        if i == 0:
            continue
        filename = f'html/{html_file}.{len(png_found)+1}.png'
        web_filename = f'{html_file.split("sums/")[1]}.{len(png_found)+1}.png'
        for img in doc.get_page_images(i):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n < 5:  # this is GRAY or RGB
                pix.save(filename)  # pix.save("p%s-%s.png" % (i, xref))
            else:  # CMYK: convert to RGB first
                pix1 = fitz.Pixmap(fitz.csRGB, pix)
                pix1.save(filename)  # pix1.save("p%s-%s.png" % (i, xref))
            png_found.append(web_filename)
            break
        if len(png_found) == 2:
            break

    print('images are:', png_found)
    return png_found


def archive(filename):
    with open('html/' + filename, 'r') as f:
        lines = f.readlines()
    lines = [line for line in lines if line]
    if len(lines) <= 80:
        return
    archive_file = filename + '_' + str(random.randint(1, 100_000))
    with open('html/' + archive_file, 'w') as f:
        f.write(lines[0])
        for line in lines[40:]:
            f.write(line + '\n')
    with open('html/' + filename, 'w') as f:
        for line in lines[:40]:
            f.write(line + '\n')
        f.write(f'<h1><a href="{archive_file}">More</a></h1>\n')


def sort(filename):
    with open('html/' + filename, 'r') as f:
        lines = f.readlines()
    lines = [line for line in lines if line]
    contents = [line for line in lines if line.startswith('<a')]
    header = [line for line in lines if line.startswith('<html')]
    footer = [line for line in lines if line.startswith('<h1')]
    return
    with open('html/' + filename, 'w') as f:
        for line in header:
            f.write(line + '\n')
        for line in contents.reverse():
            f.write(line + '\n')
        for line in footer:
            f.write(line + '\n')


def lockfile(link):
    file = 'pids/wip' + link + '.lck'
    return file


def lock_article(link):
    file = lockfile(link)
    if os.path.exists(file):
        return False
    with open(file, 'w') as f:
        f.write(str(os.getpid()))
        return True


def unlock_article(link):
    file = lockfile(link)
    with open(file) as f:
        pid = int(f.read())
    if pid == os.getpid():
        os.remove(file)

parser = argparse.ArgumentParser(description='Description of your program')
parser.add_argument('-t','--theme', help='all or theme: LG, AI, etc.', default='LG')
parser.add_argument('-n','--number', help='number of articles per theme', type=int, default=1)
args = vars(parser.parse_args())

durations = datetime.timedelta(0)
openpages = 0

def lookup(ref="/list/cs.LG/recent", theme="main"):
    global openpages
    global durations
    links = set()
    url = "https://arxiv.org" + ref
    index_html = 'html/index.html'
    filename = ref.replace('/', '_') + '.html'
    disk_filename = 'html/' + filename
    r = session.get(url)
    pages = r.html.find('.list-identifier a')
    for page in pages:
        links = links | { l for l in page.links if l.startswith('/abs') }
    # if not (('cs.LG' in ref) or ('cs.LG' in ref)):
    if args['theme'] == 'all':
        print("all themes")
        n = args['number']
        links = sorted(links, reverse=True)[:n]
    else:
        if 'cs.' + args['theme'] in ref:
            links = sorted(links, reverse=True)[:20]
        else:
            print(f"skipping, {args['theme']} not in {ref}")
            return
    print(ref, links)
    if not os.path.exists(disk_filename):
        with open(disk_filename, 'w') as f:
            f.write(header + '<body><h1><a href="index.html">abstract</a></h1>\n')
    archive(filename)
    try:
        for i, link in enumerate(links):
            if not lock_article(link):
                print(os.getpid(), "skipping, other process does it")
                continue
            card_cache = 'cache' + link + '.json'
            if os.path.exists(card_cache):
                print(os.getpid(), "skipping, cached already")
                unlock_article(link)
                continue
            url = 'https://arxiv.org' + link
            try:
                start = datetime.datetime.now()
                plot, summary, image = openpage(link, theme=theme)
                duration = datetime.datetime.now() - start
                if duration.seconds > 20:
                    openpages += 1
                    durations += duration
                print('duration: ', str(duration), 'avg', str(durations/openpages))
            except Exception as e:
                logger(e, f"{link} from theme {theme}")
                print(os.getpid(), "skipping, openpage failed")
                unlock_article(link)
                continue
            card = f'<a class="media" href="{url}" target="_blank"><h2>{plot}</h2><img class="media-object" src="{image}"/><p class="media-body">{summary}</p></a>\n'
            # extract first to index
            record = dict(url=url, ref=link.split('/')[-1], plot=plot, image=image, theme=theme, summary=summary)
            if i == 0:
                index_cache = 'cache/idx' + link + '.json'
                with open(index_cache, 'w') as f:
                    f.write(json.dumps(record))
            if os.path.exists(card_cache):
                unlock_article(link)
                print(os.getpid(), "skipping, index written")
                continue
            with open(disk_filename, 'a') as f:
                f.write(card)
                with open(card_cache, 'w') as f:
                    f.write(json.dumps(record))
            print(os.getpid(), "done, unlocking")
            unlock_article(link)
    except KeyboardInterrupt:
        print("exiting...")
        sort(filename)
        print("ok...")
        sys.exit(0)
    finally:
        sort(filename)
        # with open(disk_filename, 'a') as f:
        #     f.write('</head></html>')

    print("done")

def sections(url='https://arxiv.org/'):
    r = session.get(url)
    links = r.html.find('a')
    links_to_scan = [link for link in links if link.attrs.get('id') and link.attrs['id'].startswith('cs.')]
    for link in tqdm(links_to_scan):
        # print(link.attrs.get('id'))
        relative_link = link.attrs['href']
        print(relative_link)
        theme = link.text.split('\n')[0].split(';')[0]
        print(theme)
        print('*'*80)
        lookup(ref=relative_link, theme=theme)


sections()

# extract_pdf('_pdf_2105.00171', title="title sample")
