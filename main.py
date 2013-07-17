# -*- coding: utf-8 -*-

import os
import json
import sys
import shutil
import SocketServer
import SimpleHTTPServer
from datetime import datetime

import jinja2
from markdown import markdown

env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
markdown_options = ['extra', 'codehilite']
args = {'arghelp': 'arguments help',
        'init': 'initialize the blog folder',
        'post': 'create new post',
        'page': 'create new page',
        'update': 'generate the static html',
        'server': 'preview the html'}


def dateformat(value, format_str):
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return value.strftime(format_str).format(value.day)


env.filters['dateformat'] = dateformat


def get_gconf():
    return json.loads(open('blog/config.json', 'r').read())


def makedir(path, ifrm=False):
    if ifrm:
        if os.path.exists(path):
            shutil.rmtree(path)
    try:
        os.makedirs(path)
    except:
        pass


def copy(src, dst, isrm=False):
    if os.path.isdir(src):
        if isrm:
            if os.path.exists(dst):
                shutil.rmtree(dst)
        try:
            shutil.copytree(src, dst)
        except:
            pass
    else:
        if os.path.exists(dst):
            if isrm:
                os.remove(dst)
                shutil.copyfile(src, dst)
        else:
            shutil.copyfile(src, dst)


def init():
    makedir('blog')
    copy('config.json', 'blog/config.json')
    copy('templates/css', 'blog/css', True)
    copy('templates/js', 'blog/js', True)


def server():
    os.chdir('blog')
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('', 8000), handler)
    print 'please visit http://127.0.0.1:8000'
    httpd.serve_forever()


def arghelp():
    print 'valid args:'
    for k, v in args.iteritems():
        print '%s  -->  %s' % (k, v)


def post(*args):
    path = 'blog/src/post/%s' % args[0]
    makedir(path)
    copy('post.json', path + '/post.json')
    if not os.path.exists(path + '/post.md'):
        with open(path + '/post.md', 'w') as f:
            f.write('##hello world!')


def page(*args):
    path = 'blog/src/page/%s' % args[0]
    makedir(path)
    copy('post.json', path + '/page.json')
    if not os.path.exists(path + '/page.md'):
        with open(path + '/page.md', 'w') as f:
            f.write('##hello world!')


def render(template, **params):
    global_conf = get_gconf()
    params.update(**global_conf)
    return env.get_template(template).render(**params)


def get_content(md, template, **params):
    html = markdown(md, markdown_options)
    return html


def get_single(path, url, ptype='post'):
    conf = json.loads(open(path + '/' + ptype + '.json', 'r').read())
    conf.update({'path': path, 'url': url})
    md = open(path + '/' + ptype + '.md', 'r').read()
    content = get_content(md, ptype + '.html', **conf)
    conf.update({'content': content})
    return conf


def feeds(posts):
    blogs = []
    for p in posts[:10]:
        blogs.append(get_single(p['path'], p['url']))
    with open('blog/atom.xml', 'w') as f:
        f.write(render('atom.xml', blogs=blogs, now=datetime.now()))


def walk(path):
    if not os.path.exists(path):
        return []
    files = map(lambda x: os.path.join(path, x), os.listdir(path))
    mds = filter(lambda x: x.endswith('.md'), files)
    dirs = filter(lambda x: os.path.isdir(x), files)
    ret = []
    if mds:
        ret.append(path)
    for d in dirs:
        ret.extend(walk(d))
    return ret


def gen(posts, ptype):
    for p in posts:
        path = 'blog/' + p['path'][14:]
        makedir(path)
        if os.path.exists(p['path'] + '/img'):
            copy(p['path'] + '/img', path + '/img')
        with open(path + '/index.html', 'w') as f:
            conf = get_single(p['path'], p['url'], ptype)
            f.write(render(ptype + '.html', **conf))


def home(path, template, posts, **params):
    gconf = get_gconf()
    per_page = gconf['number_of_posts_per_page']
    total_page = (len(posts) - 1) / per_page + 1
    for i in range(total_page):
        tmp_path = path
        if i > 0:
            tmp_path = path + ('/page/%d' % (i + 1))
        makedir(tmp_path)
        offset = i * per_page
        limit = offset + per_page
        ps = [get_single(p['path'], p['url']) for p in posts[offset:limit]]
        with open(tmp_path + '/index.html', 'w') as f:
            params.update({'posts': ps, 'total': len(posts)})
            f.write(render(template, **params))


def search(posts):
    ret = []
    for p in posts:
        conf = get_single(p['path'], p['url'])
        ret.append({'title': conf['title'],
                    'tags': conf['tags'],
                    'date': conf['date'],
                    'url': conf['url']})
    with open('blog/search.json', 'w') as f:
        f.write(json.dumps(ret))


def update():
    posts_path = walk('blog/src/post')
    pages_path = walk('blog/src/page')
    posts = [{'path': path, 'url': '/' + path} for path in posts_path]
    pages = [{'path': path, 'url': '/' + path} for path in pages_path]
    feeds(posts)
    gen(posts, 'post')
    gen(pages, 'page')
    search(posts)
    home('blog', 'home.html', posts)
    tags = {}
    for p in posts:
        conf = get_single(p['path'], p['url'])
        for tag in conf['tags'].split():
            if tag not in tags:
                tags[tag] = []
            tags[tag].append(conf)
    for tag, posts in tags.iteritems():
        home('blog/tag/%s' % tag, 'tag.html', posts, tag=tag)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in args:
        arghelp()
    else:
        eval(sys.argv[1])(*sys.argv[2:])
