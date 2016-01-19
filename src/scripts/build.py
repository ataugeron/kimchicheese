#!/usr/bin/env python
import argparse
import codecs
import jinja2
import json
import markdown
import os
import shlex
import shutil
import subprocess

ROOT_FOLDER = os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
SRC_FOLDER = os.path.join(ROOT_FOLDER, 'src')
SITE_FOLDER = os.path.join(ROOT_FOLDER, 'site')

CSS_FOLDER = os.path.join(SRC_FOLDER, 'css')
IMAGES_FOLDER = os.path.join(SRC_FOLDER, 'images')
ASSETS_FOLDERS = [CSS_FOLDER, IMAGES_FOLDER]

ESSAYS_FOLDER = os.path.join(SRC_FOLDER, 'essays')
ESSAYS_METADATA_PATH = os.path.join(ESSAYS_FOLDER, 'essays.json')

TEMPLATES_FOLDER = os.path.join(SRC_FOLDER, 'templates')

templatesLoader = jinja2.FileSystemLoader(TEMPLATES_FOLDER)
templatesEnvironment = jinja2.Environment(loader=templatesLoader)


class Essay(object):

    def __init__(self, key, metadata):
        self.key = key
        self.title = metadata['title']
        self.subtitle = metadata['subtitle']
        self.displaySubtitle = metadata.get('displaySubtitle', True)
        self.relatedEssays = metadata['relatedEssays']
        self.pageName = '{key}.html'.format(key=key)
        self.imageName = '{key}.jpg'.format(key=key)
        self.body = self.loadBody()

    def loadBody(self):
        for filename in os.listdir(ESSAYS_FOLDER):
            key, ext = filename.split(os.extsep)
            if key == self.key:
                path = os.path.join(ESSAYS_FOLDER, filename)
                with codecs.open(path, encoding='utf-8') as f:
                    data = f.read()
                if ext == 'html':
                    html = data
                elif ext == 'md':
                    html = markdown.markdown(data, output_format='html5')
                else:
                    raise NotImplementedError('Rendering not implemented for {ext} files'.format(ext=ext))
                return html
        raise KeyError('Could not find content file for essay "{key}"'.format(key=self.key))


def createSiteFolder():
    if os.path.exists(SITE_FOLDER):
        shutil.rmtree(SITE_FOLDER)
    os.mkdir(SITE_FOLDER)

def loadEssays():
    with open(ESSAYS_METADATA_PATH) as f:
        metadata = json.loads(f.read())
        return metadata['index'], {key:Essay(key, jsonDict) for key, jsonDict in metadata['essays'].iteritems()}

def renderFile(name, template, context):
    path = os.path.join(SITE_FOLDER, name)
    with codecs.open(path, mode='w', encoding='utf-8') as f:
        html = template.render(context)
        f.write(html)

def buildIndex(index, essays):
    template = templatesEnvironment.get_template('index.html')
    context = {'essays': [essays[key] for key in index]}
    renderFile('index.html', template, context)

def buildEssays(essays):
    for key, essay in essays.iteritems():
        relatedEssays = [essays[key] for key in essay.relatedEssays]
        template = templatesEnvironment.get_template('essay.html')
        context = {'essay': essay, 'relatedEssays': relatedEssays}
        renderFile(essay.pageName, template, context)

def copyAssets():
    for src in ASSETS_FOLDERS:
        dst = os.path.join(SITE_FOLDER, os.path.basename(src))
        shutil.copytree(src, dst)

def buildSite():
    createSiteFolder()
    index, essays = loadEssays()
    buildIndex(index, essays)
    buildEssays(essays)
    copyAssets()

def publishSite():
    commands = [
        'git stash',
        'git checkout gh-pages',
        'cp -r site/* .',
        'git add --all .',
        'git commit -m "Generate website (auto)"',
        'git push origin gh-pages',
        'git checkout master',
        'git stash pop',
    ]
    command = '; '.join(commands)
    subprocess.Popen(command, shell=True, cwd=ROOT_FOLDER).wait()

def openSite():
    indexPath = os.path.join(SITE_FOLDER, 'index.html')
    os.system('open {indexPath}'.format(indexPath=indexPath))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--open', action='store_true')
    args = parser.parse_args()

    buildSite()
    if args.publish:
        publishSite()
    if args.open:
        openSite()
