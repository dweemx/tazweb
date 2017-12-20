from html.parser import HTMLParser
import re
import json
import os

# create a subclass and override the handler methods
class HTML2JSONConverter(HTMLParser):
    
    tmp = []
    body = []
    print_log=False
    
    def handle_starttag(self, tag, attrs):    
        nbr_tags = len(self.tmp)
        
        # Followig tags should be closed directly and not waiting for an and tag
        if nbr_tags > 0 and self.tmp[nbr_tags-1].tag in ["img","input","link"]:
            self.tmp.pop()
            return
                
        """ Handle code errors: missing end tags """
        html_tag = HTMLTag(tag)
        
        if nbr_tags == 0:
            self.body.append(html_tag)
        
        if nbr_tags > 0:
            # th, td html tags have a tr html tag as parent
            if tag in ["th","td"] and self.tmp[nbr_tags-1].tag != "tr":
                if self.print_log:
                    print("ERROR: ", tag, "does not have a tr as parent")
                self.tmp.pop()
                nbr_tags -= 1
        
        if nbr_tags > 0:
            self.tmp[nbr_tags-1].append_child(html_tag)
        self.tmp.append(html_tag)
        
        for attr in attrs:
            # attr is an array with attr[0] is the key and attr[1] the value
            html_tag.add_attribute(attr[0], attr[1])
        
        # Followig tags should be closed directly and not waiting for an and tag
#         if html_tag.tag in ["img","input","link"]:
#             self.tmp.pop()

    def handle_endtag(self, tag):        
        nbr_tags = len(self.tmp)
        if self.tmp[nbr_tags-1].tag != tag:
            if self.print_log:
                print("ERROR: last tag is different from current tag (", self.tmp[nbr_tags-1].tag, " >< ", tag, ")")
        if nbr_tags > 0:
            self.tmp.pop()

    def handle_data(self, data):
        if len(data) == 1:
            if ord(data) == 32:
                return
        nbr_tags = len(self.tmp)
        self.tmp[nbr_tags-1].add_data('"'+data+'"')
#         print "Encountered some data  :", data
    
    def get_body(self):
        body = []
        for tag in self.body:  
            json_str = tag.__str__()
#             print json_str
            # Convert JSON string to JSON object : http://stackoverflow.com/questions/4528099/convert-string-to-json-using-python
            body.append(json.loads(json_str))
        
        # Empty the variables
        del self.tmp[:]
        del self.body[:]
        return body    

class HTMLTag():
        
    def __init__(self,tag):
        # If declared outside it will be considered as a static variable
        self.tag = tag
        self.content = []
        self.attrs = {}
        
    def add_data(self,data):
        self.content.append(data)
    
    def append_child(self,tag):
#         print "Parent of ",tag.tag,": ",self.tag, "(",len(self.content),")"
        self.content.append(tag)
    
    def add_attribute(self,key,value):
        self.attrs[key] = value
        
    # http://stackoverflow.com/questions/727761/python-str-and-lists     
    def __str__(self):
        c = ','.join(str(p) for p in self.content)
        # Concatenate strings : http://www.pythonforbeginners.com/concatenation/string-concatenation-and-formatting-in-python
        return '{"tag":"%s","attributes":%s,"content":[%s]}' % (self.tag,json.dumps(self.attrs),c)
        
    def __repr__(self):
        return self.__str__()
    

class TazWeb():
    
    def __init__(self,html):
        if not os.path.exists("tmp"):
            os.makedirs("tmp")
        self.html = html
        # instantiate the parser and fed it some HTML
        self.parser = HTML2JSONConverter()
        self.parser.feed(html)
 
    # Get JSON
    def get_json(self):
        return self.parser.get_body()

def format_html(_html):
    # Remove tabs and newlines: http://stackoverflow.com/questions/16355732/how-to-remove-tabs-and-newlines-with-a-regex
    # Convert bytes to string http://stackoverflow.com/questions/606191/convert-bytes-to-a-python-string
    html = re.sub(r"\s+", " ", _html)
    # Remove shortest match: http://stackoverflow.com/questions/11301387/python-regex-first-shortest-match
    # Remove script containers
    html = re.sub(r'<script ?.*?>.*?</script>', '', html)
    # # Remove head containers
    html = re.sub(r'<head>.*?</head>', '', html)
    html = re.sub(r">\s+<", "><", html)
    # # Remove comments
    # html = re.sub(r"<\!--.*?-->", "", html)
    # Trim: http://stackoverflow.com/questions/761804/trimming-a-string-in-python
    html = html.strip()
    return html
          
def parse_path(path):
    """"""
    p = []
    sub_paths = path.split('>')
    for sub_path in sub_paths:
        sub_path = sub_path.strip()
        _attrs = []
                
        m = re.search('(.+?)\[(.+?)\]',sub_path)
        if m:
            tag = m.group(1)
            attrs = m.group(2)
            if "," in attrs: 
                for attr in attrs.split(","):
                    key,value = attr.strip().split("=")
            else:
                key,value = attrs.strip().split("=")
                _attrs.append({"key":key,"value":value})
            p.append({"tag":tag,"attrs":_attrs})
            continue
        
        # Check for id attribute reference 
        m = re.search('(.+?)#(.+?)',sub_path)
        if m:
            tag = m.group(1)
            _attrs = {"key":"id","value":m.group(2)}
            p.append({"tag":tag,"attrs":_attrs})
            continue
        
        # Check for class attribute reference
        m = re.search('(.+?)\.(.+?)',sub_path)
        if m:
            tag = m.group(1)
            _attrs = {"key":"class","value":m.group(2)}
            p.append({"tag":tag,"attrs":_attrs})
            continue
        
        p.append({"tag":sub_path,"attrs":_attrs})
     
    return p

def json_search(json,path,no_html=False):
    objs_found = []
    
    if isinstance(json, dict):
        objs_found_tmp = json["content"][:] # Copy the object (not a reference!)
    else:
        objs_found_tmp = json[:] # Copy the object (not a reference!)
    
    pp = parse_path(path)
    
    step = 0
    for sp in pp:  
        step += 1          
        def s(sp,tmp_obj):
            
            del objs_found_tmp[:]
                                    
            for t in tmp_obj:
                                                
                if not isinstance(t, dict):
                    continue
                                            
                if t["tag"] != sp["tag"]:
                    continue
                            
                if len(sp["attrs"]) > 0:
                    
                    attrs_verified = 0
                    
                    for attr in sp["attrs"]:
                        if attr["key"] not in t["attributes"]:
                            continue
                        else:
                            if attr["value"] == "*" or attr["value"] == t["attributes"][attr["key"]]:
                                attrs_verified += 1
                            elif "*" in attr["value"]:
                                if re.search(attr["value"].replace("*","(.+?)"),t["attributes"][attr["key"]]):
                                    attrs_verified += 1
                            else:
                                continue
                    
                    if attrs_verified != len(sp["attrs"]):
                        continue
                
                # Append vs Extend : http://stackoverflow.com/questions/252703/append-vs-extend
                objs_found_tmp.extend(t["content"])
                
#                 print t["attributes"], pp.index(sp), (len(pp)-1)
#                 print t["attributes"], step, (len(pp))
                
                if step == len(pp):
                    if no_html:
                        text = ""
                        for x in t["content"]:
                            if isinstance(x, dict):
                                text += x["content"][0]
                            else:
                                text += x
                        objs_found.append(text)
                    else:
                        objs_found.append(t)
        # Put value instead of reference: http://stackoverflow.com/questions/8122627/the-copy-variable-changes-the-original-var-in-python
        s(sp,objs_found_tmp[:])
                     
    if len(objs_found) < 1:
        print("Nothing found!")
    else:
        if no_html:
            return ''.join(objs_found)
        return objs_found