################################################################################
#   Libraries                                                                  #
################################################################################
import os, time, codecs, hashlib
################################################################################
from bs4 import BeautifulSoup
################################################################################
from flask import Flask, flash, redirect, render_template, request, session, abort, url_for
################################################################################
from htmlmin.main import minify
################################################################################
from muncher.config import Config
################################################################################
from muncher.muncher import Muncher

################################################################################
#   Encrypt_String                                                             #
################################################################################

def encrypt_string(hash_string):
    sha_signature = \
        hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

################################################################################
#   App                                                                        #
################################################################################

app = Flask(__name__)

################################################################################
#   Minify and Muncher "Rendering" HTML                                        #
################################################################################

@app.after_request
def response_minify(response):
    """
    minify and muncher html
    """
    if response.content_type == u'text/html; charset=utf-8':
        template = None
        if str(request.path)=='/view1' or str(request.path)=='/view2' :
            #Extractor of CSS Links
            soup = BeautifulSoup(response.get_data(as_text=True),features='html.parser')
            cssGroupLinks = ''
            #Find the lines with the word 'link'
            for link in soup.find_all('link'):
                #If you find the substring 'CSS' in it then ..
                if 'css' in link.get('href'):
                    #Get the link
                    link_css = link.get('href')
                    #Get file fullpath
                    file_fpath = str(os.getcwd())+link_css.replace('/','\\')
                    #Generate a custom concatenate for Muncher
                    if cssGroupLinks == '':
                        cssGroupLinks = file_fpath
                    else:
                        cssGroupLinks = cssGroupLinks + ',' + file_fpath

            #Name of the file encrypted with the unix time and the ip address of the browser
            file_tmp = encrypt_string(str(time.time()) + request.remote_addr)
            #Html Compressor
            compress_site = minify(response.get_data(as_text=True))
            #Search and replace the css original with the new compiled.
            compress_site = compress_site.replace('.css', '.opt.css')
            #Deposit tmp file for Muncher
            temp_html_file = open("tmp/"+file_tmp+".html","w")
            temp_html_file.write(compress_site)
            temp_html_file.close()

            #Get files fullpath
            template = str(os.getcwd())+'\\tmp\\'+file_tmp+".html"
            template_compiled = str(os.getcwd())+'\\tmp\\'+file_tmp+".opt.html"

            #Add array for Muncher
            list = []
            list.append(('--css', cssGroupLinks.encode('UTF8')))
            list.append(('--html',template))

            #Run Muncher...
            config = Config()
            config.processArgs(list)
            muncher = Muncher(config)
            muncher.run()

            #Open Result with BeautifulSoup
            f=codecs.open(template_compiled, 'r', 'utf-8')
            #Load in a tmp_compiled
            tmp_compiled = BeautifulSoup(f.read())

            #Show Minify and Muncher Site!
            response.set_data(
                tmp_compiled
            )

        else:
            response.set_data(
                minify(response.get_data(as_text=True))
            )

        return response
    return response

################################################################################
#   Route Index                                                                #
################################################################################

@app.route('/')
def home():
    return """
           Test View1  <a href='/view1'>Check It!</a>
           Test View2  <a href='/view2'>Check It!</a>
           """

################################################################################
#   View1                                                                      #
################################################################################

@app.route('/view1')
def view1():
    return render_template('view1.html')

################################################################################
#   View1                                                                      #
################################################################################

@app.route('/view2')
def view2():
    return render_template('view2.html')

################################################################################
#  __main__                                                                    #
################################################################################
if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='0.0.0.0', port=4000)
