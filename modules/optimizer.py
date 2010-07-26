#!/usr/bin/python

# Copyright 2010 Craig Campbell
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, re, glob, os
from util import Util
from minimizer import Minimizer
from varfactory import VarFactory

class Optimizer(object):
    ids = []
    classes = []
    id_map = {}
    class_map = {}

    def __init__(self, config):
        """constructor

        Returns:
        void

        """
        self.config = config

    @staticmethod
    def showUsage():
        """shows usage information for this script"""
        print "USAGE:"
        print "./optimize.py path/to/css path/to/views"
        print "OR"
        print "./optimize.py path/to/single/file.html\n"
        print "OPTIONAL PARAMS:"
        print "--css-file {file_name}       file to use for optimized css (defaults to optimized.css)"
        print "--view-ext {extension}       sets the extension to look for the view directory (defaults to html)"
        print "--rewrite-css                if this arg is present then header css includes are rewritten in the new views"
        print "--help                       shows this menu"
        sys.exit(2)

    def setupFiles(self):
        """sets up files for this run by deleting directories/files created in previous runs

        Returns:
        void

        """
        Util.unlink(self.config.getCssFile())
        Util.unlink(self.config.getCssMinFile())
        Util.unlinkDir(self.config.view_dir + "_optimized")

    def addIds(self, ids):
        """adds a list of ids to the master id list to replace

        Arguments:
        ids -- list of ids to add

        Returns:
        void

        """
        for id in ids:
            if id[1] is ';':
                continue
            if id[0] not in self.ids:
                self.ids.append(id[0])

    def addClasses(self, classes):
        """adds a list of classes to the master class list to replace

        Arguments:
        classes -- list of classes to add

        Returns:
        void

        """
        for class_name in classes:
            if class_name not in self.classes:
                self.classes.append(class_name)

    def processFile(self, path):
        """processes a single css file to find all classes and ids to replace

        Arguments:
        path -- path to css file to process

        Returns:
        Void

        """
        contents = Util.fileGetContents(path)

        ids_found = re.findall(r'(#\w+)(;)?', contents)
        classes_found = re.findall(r'(?!\.[0-9])\.\w+', contents)

        self.addIds(ids_found)
        self.addClasses(classes_found)

    def processStyles(self):
        """gets all files from config and processes them to see what to replace

        Returns:
        void

        """
        files = self.config.getCssFiles()
        for file in files:
            self.processFile(file)

    def processMaps(self):
        """loops through classes and ids to process to determine shorter names to use for them
        and creates a dictionary with these mappings

        Returns:
        void

        """
        for class_name in self.classes:
            self.class_map[class_name] = "." + VarFactory.getNext("class")

        for id in self.ids:
            self.id_map[id] = "#" + VarFactory.getNext("id")

    def optimizeHtml(self, path, rewrite_css):
        """replaces classes and ids with new values in an html file

        Uses:
        Optimizer.replaceHtml

        Arguments:
        path -- string path to file to optimize
        rewrite_css -- boolean whether or not we should also rewrite <link href attributes

        Returns:
        string

        """
        html = Util.fileGetContents(path)
        html = self.replaceHtml(html)
        html = self.optimizeCssBlocks(html)
        html = self.optimizeJavascriptBlocks(html)

        if rewrite_css is True:
            html = self.rewriteHeaderCss(html)

        return html

    def replaceHtml(self, html):
        """replaces classes and ids with new values in an html file

        Arguments:
        html -- contents to replace

        Returns:
        string

        """
        html = self.replaceHtmlIds(html)
        html = self.replaceHtmlClasses(html)
        return html

    def replaceHtmlIds(self, html):
        """replaces any instances of ids in html markup

        Arguments:
        html -- contents of file to replaces ids in

        Returns:
        string

        """
        for key, value in self.id_map.items():
            key = key[1:]
            value = value[1:]
            html = html.replace("id=\"" + key + "\"", "id=\"" + value + "\"")

        return html

    def replaceHtmlClasses(self, html):
        """replaces any instances of classes in html markup

        Arguments:
        html -- contents of file to replace classes in

        Returns:
        string

        """
        for key, value in self.class_map.items():
            key = key[1:]
            value = value[1:]
            class_blocks = re.findall(r'class="(.*)"', html)
            for class_block in class_blocks:
                new_block = class_block.replace(key, value)
                html = html.replace("class=\"" + class_block + "\"", "class=\"" + new_block + "\"")

        return html

    def optimizeCssBlocks(self, html):
        """rewrites css blocks that are part of an html file

        Arguments:
        html -- contents of file we are replacing

        Returns:
        string

        """
        result_css = ""
        matches = self.getCssBlocks(html)
        for match in matches:
            match = self.replaceCss(match)
            result_css = result_css + match

        result_css = Minimizer.minimize(result_css)

        if len(matches):
            return html.replace(matches[0], result_css)

        return html

    def getCssBlocks(self, html):
        """searches a file and returns all css blocks <style type="text/css"></style>

        Arguments:
        html -- contents of file we are replacing

        Returns:
        list

        """
        return re.compile(r'\<style type=\"text\/css\"\>(.*?)\<\/style\>', re.DOTALL).findall(html)

    def optimizeCss(self, paths):
        """takes a bunch of css files and combines them into one
        
        Arguments:
        paths -- list of css file paths
        
        Returns:
        string
        
        """
        combined_css = ""
        for path in paths:
            print "adding " + path + " to " + self.config.getCssFile()
            css = Util.fileGetContents(path)
            css = self.replaceCss(css)
            combined_css = combined_css + "/*\n * " + path + "\n */\n" + css + "\n\n"

        return combined_css

    def replaceCss(self, css):
        """single call to handle replacing ids and classes

        Arguments:
        css -- contents of file to replace

        Returns:
        string

        """
        css = self.replaceCssFromDictionary(self.class_map, css)
        css = self.replaceCssFromDictionary(self.id_map, css)
        return css

    def replaceCssFromDictionary(self, dictionary, css):
        """replaces any instances of classes and ids based on a dictionary

        Arguments:
        dictionary -- map of classes or ids to replace
        css -- contents of css to replace

        Returns:
        string

        """
        for key, value in dictionary.items():
            css = css.replace(key + "{", value + "{")
            css = css.replace(key + " {", value + " {")
            css = css.replace(key + "#", value + "#")
            css = css.replace(key + " #", value + " #")
            css = css.replace(key + ".", value + ".")
            css = css.replace(key + " .", value + " .")
            css = css.replace(key + ",", value + ",")
            css = css.replace(key + " ", value + " ")

        return css

    def optimizeJavascriptBlocks(self, html):
        """rewrites javascript blocks that are part of an html file

        Arguments:
        html -- contents of file we are replacing

        Returns:
        string

        """
        matches = self.getJsBlocks(html)

        for match in matches:
            new_js = self.replaceJavascript(match)
            html = html.replace(match, new_js)

        return html

    def getJsBlocks(self, html):
        """searches a file and returns all javascript blocks: <script type="text/javascript"></script>

        Arguments:
        html -- contents of file we are replacing

        Returns:
        list

        """
        return re.compile(r'\<script type=\"text\/javascript\"\>(.*?)\<\/script\>', re.DOTALL).findall(html)

    def replaceJavascript(self, js):
        """single call to handle replacing ids and classes

        Arguments:
        js -- contents of file to replace

        Returns:
        string

        """
        js = self.replaceJsFromDictionary(self.id_map, js)
        js = self.replaceJsFromDictionary(self.class_map, js)
        return js

    def replaceJsFromDictionary(self, dictionary, js):
        """replaces any instances of classes and ids based on a dictionary

        Arguments:
        dictionary -- map of classes or ids to replace
        js -- contents of javascript to replace

        Returns:
        string

        """
        for key, value in dictionary.items():
            blocks = re.findall(r'\((\'|\")(.*)(\'|\")\)', js)
            for block in blocks:
                new_block = block[1].replace(key, value)
                js = js.replace("(" + block[0] + block[1] + block[2] + ")", "(" + block[0] + new_block + block[2] + ")")

        return js

    def rewriteHeaderCss(self, html):
        """rewrites <link href tags in header to use new optimized css path

        Arguments:
        html -- contents of the file we are replacing

        Returns:
        string

        """
        new_lines = []
        i = 0
        prefix = ""

        base_view_path = Util.getBasePath(self.config.view_dir)
        base_css_path = Util.getBasePath(self.config.css_dir)

        if base_css_path == base_view_path:
            prefix = ".."

        for line in html.split("\n"):
            if "link href" not in line or "text/css" not in line:
                new_lines.append(line)
                continue

            if i is 0:
                css_min_file = self.config.getCssMinFile().replace(base_view_path, "")
                new_lines.append('    <link href="' + prefix + css_min_file + '" rel="stylesheet" type="text/css" />')
                i = i + 1

        html = "\n".join(map(str, new_lines))
        return html

    def run(self):
        """runs the optimizer and does all the magic

        Returns:
        void

        """
        self.processStyles()
        self.processMaps()

        # first optimize all the css files
        css = self.optimizeCss(self.config.getCssFiles())
        minimized_css = Minimizer.minimize(css)
        Util.filePutContents(self.config.getCssFile(), css)
        Util.filePutContents(self.config.getCssMinFile(), minimized_css)

        # next optimize the views
        paths = self.config.getViewFiles()
        os.mkdir(self.config.view_dir + "_optimized")
        for path in paths:
            html = self.optimizeHtml(path, self.config.rewrite_css)
            Util.filePutContents(self.config.view_dir + "_optimized/" + path.split("/").pop(), html)


class OptimizerSingleFile(Optimizer):
    """child class of Optimizer to handle processing a single file"""
    def setupFiles(self):
        """overwrites parent setupFiles() method

        Returns:
        void

        """
        ext = Util.getExtension(self.config.single_file_path)
        self.config.single_file_opt_path = self.config.single_file_path.replace("." + ext, ".opt." + ext)
        Util.unlink(self.config.single_file_opt_path)

    def run(self):
        """overwrites parent run() method

        Returns:
        void

        """
        self.processStyles()
        self.processMaps()
        html = self.optimizeHtml(self.config.single_file_path, False)
        Util.filePutContents(self.config.single_file_opt_path, html);


class Config(object):
    """configuration object for handling all config options for css-optimizer"""
    def __init__(self):
        """config object constructor

        Returns:
        void

        """
        self.single_file_mode = False
        self.css_file = "optimized.css"
        self.view_extension = "html"
        self.rewrite_css = False
        self.ids_to_replace = []
        self.classes_to_replace = []
        relative_path = ""

    def getArgCount(self):
        """gets the count of how many arguments are present

        Returns:
        int

        """
        return len(sys.argv)

    def getCssFile(self):
        """gets the path to the css file to write all the combined css to

        Returns:
        string

        """
        return self.css_dir + "/" + self.css_file

    def getCssMinFile(self):
        """gets the path to write the minimized css file to

        Returns:
        string

        """
        return self.getCssFile().replace(".css", ".min.css");

    def getCssFiles(self):
        """gets all css files to process for this run

        Returns:
        list

        """
        files = []
        if self.single_file_mode is True:
            files.append(self.single_file_path)
            return files

        return glob.glob(self.css_dir + "/*.css")

    def getViewFiles(self):
        """gets all view files to process for this request

        Returns:
        list

        """
        files = []
        if self.single_file_mode is True:
            files.append(self.single_file_path)
            return files

        return glob.glob(self.view_dir + "/*." + self.view_extension)

    def processArgs(self):
        """processes arguments passed in via command line and sets config settings accordingly

        Returns:
        void

        """
        # if we only pass in one argument let's assume we are running in single file mode
        if self.getArgCount() == 2:
            self.single_file_mode = True
            self.single_file_path = sys.argv[1]
            if not Util.fileExists(self.single_file_path):
                print "file does not exist at path: " + self.single_file_path
                sys.exit(2)

        # required arguments
        if self.single_file_mode is False:
            try:
                self.css_dir = sys.argv[1].rstrip("/")
                self.view_dir = sys.argv[2].rstrip("/")
            except IndexError:
                Optimizer.showUsage()

        # check for optional parameters
        for key, arg in enumerate(sys.argv):
            next = key + 1
            if arg == "--help":
                Optimizer.showUsage()
            elif arg == "--rewrite-css":
                self.rewrite_css = True
            elif arg == "--css-file":
                self.css_file = sys.argv[next]
            elif arg == "--view-ext":
                self.view_extension = sys.argv[next]