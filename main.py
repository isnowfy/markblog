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
post_config = {'author': '',
               'date': '',
               'title': '',
               'tags': 'split with space'}
args = {'arghelp': 'arguments help',
        'post': 'create new post',
        'page': 'create new page',
        'update': 'generate the static html',
        'server': 'preview the html'}


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
        if isrm:
            if os.path.exists(dst):
                os.remove(dst)
        shutil.copyfile(src, dst)


def server():
    handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('', 8000), handler)
    print 'please visit http://127.0.0.1:8000'
    httpd.serve_forever()


def arghelp():
    print 'valid args:'
    for k, v in args.iteritems():
        print '%s  -->  %s' % (k, v)


def post(*args):
    path = 'post/%s' % args[0]
    makedir(path)
    copy('post.json', path + '/post.json')
    with open(path + '/post.md', 'w') as f:
        f.write('##hello world!')


def page(*args):
    path = 'page/%s' % args[0]
    makedir(path)
    copy('post.json', path + '/page.json')
    with open(path + '/page.md', 'w') as f:
        f.write('##hello world!')


def render(template, **params):
    global_conf = json.loads(open('config.json', 'r').read())
    params.update(**global_conf)
    return env.get_template(template).render(**params)


def get_content(md, template, **params):
    html = markdown(md, markdown_options)
    params.update({'html': html})
    return render(template, **params)


def get_single(path, url, ptype='post'):
    conf = json.loads(open(path + '/' + ptype + '.json', 'r').read())
    conf.update({'url': url})
    md = open(path + '/' + ptype + '.md', 'r').read()
    content = get_content(md, ptype + '.html', **conf)
    conf.update({'content': content})
    return conf


def feeds(posts):
    blogs = []
    for p in posts[:10]:
        blogs.append(get_single(p['path'], p['url']))
    makedir('blog')
    with open('blog/atom.xml', 'w') as f:
        f.write(render('atom.xml', {'blogs': blogs, 'now': datetime.now()}))


def walk(path):
    if not os.path.exists(path):
        return []
    files = map(lambda x: os.path.join(path, x), os.listdir(path))
    htmls = filter(lambda x: x.endswith('.html'), files)
    dirs = filter(lambda x: os.path.isdir(x), files)
    ret = []
    if htmls:
        ret.append(path)
    for d in dirs:
        ret.extends(walk(d))
    return ret


def gen(posts, ptype):
    for p in posts:
        makedir(p['path'])
        with open(p['path'] + '/index.html', 'w') as f:
            conf = get_single(p['path'], p['url'], ptype)
            f.write(render(ptype + '.html', **conf))


def update():
    posts_path = walk('post')
    pages_path = walk('page')
    posts = [{'path': path, 'url': '/' + path} for path in posts_path]
    pages = [{'path': path, 'url': '/' + path} for path in pages_path]
    feeds(posts)
    gen(posts)
    gen(pages)


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in args:
        arghelp()
    else:
        eval(sys.argv[1])(*sys.argv[2:])
