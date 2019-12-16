from bs4 import BeautifulSoup
import ast
import re
import json
import astor
import html
from multiprocessing import Pool
#from csharp.title_filtering.SVM import SVM

params = {
#    "langXmlFile" : "/scratch0/python_en.xml",
    "langXmlFile" : "Posts.python.xml",
#    "xmlFile" : "/scratch0/answers_en_nonzero.xml",
    "xmlFile" : "Posts.answers.xml",
    "outputFile" : "python_all.json"}

# First download and process the stackoverflow files
# os.system('wget https://archive.org/download/stackexchange/stackoverflow.com-Posts.7z')
# os.system('7z x stackoverflow.com-Posts.7z')
# 
#os.system('grep "python" Posts.xml > ' + params['langXmlFile'])
#os.system('grep "PostTypeId=\"2\"" Posts.xml > ' + params['xmlFile'])

# #   Title filtering using SVM
# s = SVM()
# s.train("../csharp/title_filtering/balanced/pos_train.txt", "../csharp/title_filtering/balanced/neg_train.txt")
# s.test("../csharp/title_filtering/balanced/pos_test.txt", "../csharp/title_filtering/balanced/neg_test.txt")

# First pass. Get the posts tagged with C#. Filter the input using a grep on c# so that this is faster
accepted_answer_re = re.compile(r"AcceptedAnswerId=\"(\d+)\"")
id_re = re.compile(r"Id=\"(\d+)\"")
title_re = re.compile(r"Title=\"([^\"]+)\"")
tags_re = re.compile(r"Tags=\"([^\"]+)\"")
body_re = re.compile(r"Body=\"([^\"]+)\"")
def process_question(line):
  acceptedanswerid = accepted_answer_re.search(line)
  if acceptedanswerid is not None and "python" in tags_re.search(line).group(1):
    return (int(acceptedanswerid.group(1)), {"id": int(id_re.search(line).group(1)), "title": title_re.search(line).group(1)})
  else:
    return None


print('finding tagged posts')
with open(params["langXmlFile"], 'r') as f:
  pool = Pool(processes=16)
  acceptedAnswers = dict([p for p in pool.map(process_question, [l for l in f]) if p is not None])

print('finding accepted answers')

def find_answers(line):
  qid = int(id_re.search(line).group(1))
  if qid in acceptedAnswers:
    return (qid, body_re.search(line).group(1))
  else:
    return None

# Pass 2, find the corresponding accepted answer
with open(params["xmlFile"], 'r') as f:
  pool = Pool(processes=16)
  codes = [p for p in pool.map(find_answers, [l for l in f]) if p is not None]
  for qid,  code in codes:
      acceptedAnswers[qid]["code"] = code

def prepare_answer_snippet(answer):
  rid, ans = answer

  if "code" not in ans:
      return None

  # Post contains an accepted answer
  if "pre" in ans["code"]:                                
    # Title is good
    #titleFilter = s.filter(ans['title'])           
    if True:#titleFilter == 0:

      soup = BeautifulSoup(html.unescape(ans["code"]), 'html.parser')
      codeTag = soup.find_all('pre')
      # Contains exactly one piece of code
      if len(codeTag) == 1:                                         
        code = codeTag[0].get_text().strip()

        # Code must be at most 1000 chars
        if (len(code) > 6 and len(code) <= 1000):                   

          # Filter out weird code snippets
          if code[0] == "<" or code[0] == "=" or code[0] == "@" or code[0] == "$" or \
            code[0:7].lower() == "select " or code[0:7].lower() == "update " or code[0:6].lower() == "alter " or \
            code[0:2].lower() == "c:" or code[0:4].lower() == "http" or code[0:4].lower() == "hkey" or \
                  re.match(r"^[a-zA-Z0-9_]*$", code) is not None:
            return None
          else:
            # Now also make sure it parses
            try:
              code = code.replace('>>>','').strip()
              ast.parse(code)
              #code = astor.dump_tree(ast.parse(code), maxline=99999, maxmerged=99999).strip()
              lines = [l for l in code.strip().split('\n') if
                          not re.match(r"^\s*(import|from|def|#)",l)
                          and l.strip()]
              if len(lines) == 1:
                code = lines[0].strip()
                return {
                    "question_id": rid,
                    "parent_answer_post_id": ans['id'],
                    "intent": ans['title'],
                    "snippet": code}
            except:
              print('parse fail')
              return None
        else:
          return None
      else:
        return None

print('starting processing')
pool = Pool(processes=16)
code_pairs = pool.map(prepare_answer_snippet, acceptedAnswers.items())

with open(params["outputFile"], 'w') as f:
  json.dump([p for p in code_pairs if p is not None], f)

# Create training and validation and test sets
#os.system('shuf python_all.txt > python_shuffled.txt')
#numLines = sum(1 for line in open('python_all.txt'))
#trainLines = int(0.8 * numLines)
#validLines = int(0.1 * numLines)
#testLines = numLines - trainLines - validLines
#os.system('head -n ' + str(trainLines) + ' python_shuffled.txt > train.txt')
#os.system('tail -n +' + str(trainLines + 1)  + ' python_shuffled.txt | head -n ' + str(validLines)  + ' > valid.txt')
#os.system('tail -n +' + str(trainLines + validLines + 1)  + ' python_shuffled.txt  > test.txt')


# Title Labeling

# This is the way I did it. Then I removed the database, so this is deprecated.

# # Get titles for manual labeling
# 
# sqlite3 Posts.sqlite3 "select a.title from Posts a, Posts b where  a.tags like '%c#%' and  a.accepted_answer_id is not null and a.accepted_answer_id = b.id and b.body like '%<code>%' and b.body not like '%<code>%<code>%' order by random() limit 1000; " > titles_1000.txt
# 
# sqlite3 Posts.sqlite3 "select a.title from Posts a, Posts b where  a.tags like '%c#%' and  a.accepted_answer_id is not null and a.accepted_answer_id = b.id and b.body like '%<code>%' and b.body not like '%<code>%<code>%'; " > titles_all.txt
# 
# 
# grep "^g " titles_1000.txt > neg.txt
# grep "^n " titles_1000.txt > pos.txt
# 
# # post
# sed -e "s/^g //" neg.txt | head -n 283 > neg_train.txt
# sed -e "s/^g //" neg.txt | tail -n 283 > neg_test.txt
# 
# sed -e "s/^n //" pos.txt | head -n 116 > pos_train.txt
# sed -e "s/^n //" pos.txt | tail -n 116 > pos_test.txt
