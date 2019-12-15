from bs4 import BeautifulSoup
import ast
import re
import json
#from csharp.title_filtering.SVM import SVM

params = {
    "langXmlFile" : "Posts.python.xml",
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

# Two pass algorithm
acceptedAnswers = {}

# First pass. Get the posts tagged with C#. Filter the input using a grep on c# so that this is faster
with open(params["langXmlFile"], 'r') as f:
  for line in f:
    y = BeautifulSoup(line, 'html.parser').row
    if y.get("acceptedanswerid") is not None and "python" in y["tags"]:
        acceptedAnswers[int(y["acceptedanswerid"])] = {"id": int(y["id"]), "title": y["title"] }

# Pass 2, find the corresponding accepted answer
with open(params["xmlFile"], 'r') as f:
  for line in f:
    # Find the first attribute enclosed in "" It should be the Id
    id1 = line.find("\"")              
    id2 = line.find("\"", id1 + 1)
    qid = int(line[(id1 + 1):id2])
    if qid in acceptedAnswers:
      y = BeautifulSoup(line, 'html.parser').row
      acceptedAnswers[qid]["code"] = y["body"]

code_pairs = []
for rid in acceptedAnswers:
  # Post contains an accepted answer
  if "pre" in acceptedAnswers[rid]["code"]:                                
    # Title is good
    #titleFilter = s.filter(acceptedAnswers[rid]['title'])           
    if True:#titleFilter == 0:

      soup = BeautifulSoup(acceptedAnswers[rid]["code"], 'html.parser')
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
            pass
          else:
            # Now also make sure it parses
            try:
              code = code.replace('>>>','')
              ast.parse(code)

              code_pairs.append({
                  "question_id": rid,
                  "parent_answer_post_id": acceptedAnswers[rid]['id'],
                  "intent": acceptedAnswers[rid]['title'],
                  "snippet": code})
            except:
              pass

with open(params["outputFile"], 'w') as f:
  json.dump(code_pairs, f)

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
