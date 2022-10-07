import re
from urllib.request import urlopen, Request
import copy
from bs4 import BeautifulSoup as soup, Tag
import spacy
def remove_unwanted_text(text):
    '''Looks for pattern  which typically starts the main text of jugement.
    The text before this pattern contains metadata like name of paries, judges and hence removed'''
    pos_list = []
    len = 0
    pos = 0
    pos_list.append(text.find("JUDGMENT & ORDER"))
    pos_list.append(text.find("J U D G M E N T"))
    pos_list.append(text.find("JUDGMENT"))
    pos_list.append(text.find("O R D E R"))
    pos_list.append(text.find("ORDER"))

    for i, p in enumerate(pos_list):

        if p != -1:
            if i == 0:
                len = 16
            elif i == 1:
                len = 15
            elif i == 2:
                len = 8
            elif i == 3:
                len = 9
            elif i == 4:
                len = 5
            pos = p + len
            break

    return pos

def get_keyword_based_preamble_end_char_offset(text):
    preamble_end_keywords = ["JUDGMENT","ORDER","J U D G M E N T","O R D E R","JUDGMENT & ORDER","COMMON ORDER","ORAL JUDGMENT"]
    preamble_end_char_offset = 0

    ### search for preamble end keywords on new lines
    for preamble_keyword in preamble_end_keywords:
        match = re.search(r'\n\s*'+preamble_keyword+r'\s*\n',text)
        if match:
            preamble_end_char_offset = match.span()[1]
            break

    #### if not found then search for the keywords anywhere
    if preamble_end_char_offset==0:
        for preamble_keyword in preamble_end_keywords:
            match = re.search(preamble_keyword, text)
            if match:
                preamble_end_char_offset = match.span()[1]
                break
    return preamble_end_char_offset

def convert_upper_case_to_title(txt):
    ########### convert the uppercase words to title case for catching names in NER
    title_tokens =  []
    for token in txt.split(' '):
        title_subtokens = []
        for subtoken in token.split('\n'):
            if subtoken.isupper():
                title_subtokens.append(subtoken.title())
            else:
                title_subtokens.append(subtoken)
        title_tokens.append('\n'.join(title_subtokens))
    title_txt = ' '.join(title_tokens)
    return title_txt

def guess_preamble_end(truncated_txt, nlp):
    ######### Guess the end of preamble using hueristics
    preamble_end = 0
    max_length = 20000
    tokens = nlp.tokenizer(truncated_txt)
    if len(tokens) > max_length:
        chunks = [tokens[i:i + max_length] for i in range(0, len(tokens), max_length)]
        nlp_docs = [nlp(i.text) for i in chunks]
        truncated_doc = spacy.tokens.Doc.from_docs(nlp_docs)
    else:
        truncated_doc = nlp(truncated_txt)
    successive_preamble_pattern_breaks = 0
    preamble_patterns_breaks_theshold = 1 ####### end will be marked after these many consecutive sentences which dont match preamble pattern
    sent_list = [sent for sent in truncated_doc.sents]
    for sent_id,sent in enumerate(sent_list):
        ###### check if verb is present in the sentence
        verb_exclusions=['reserved','pronounced','dated','signed']
        sent_pos_tag = [token.pos_ for token in sent if token.lower_ not in verb_exclusions]
        verb_present = 'VERB' in sent_pos_tag

        ###### check if uppercase or title case
        allowed_lowercase = ['for','at','on','the','in','of']
        upppercase_or_titlecase = all([token.text in allowed_lowercase or token.is_upper or token.is_title or token.is_punct for token in sent if token.is_alpha])

        if verb_present and not upppercase_or_titlecase:
            successive_preamble_pattern_breaks+=1
            if successive_preamble_pattern_breaks>preamble_patterns_breaks_theshold:
                preamble_end = sent_list[sent_id-preamble_patterns_breaks_theshold-1].end_char
                break
        else:
            if successive_preamble_pattern_breaks>0 and (verb_present or not upppercase_or_titlecase):
                preamble_end = sent_list[sent_id - preamble_patterns_breaks_theshold - 1].end_char
                break
            else:
                successive_preamble_pattern_breaks = 0

    return preamble_end

def seperate_and_clean_preamble(txt,preamble_splitting_nlp):
    ########## seperate preamble from judgment text

    ######## get preamble end offset based on keywords
    keyword_preamble_end_offset = get_keyword_based_preamble_end_char_offset(txt)
    if keyword_preamble_end_offset==0:
        preamble_end_offset = 5000 ######## if keywords not found then set arbitrarty value to reduce time for searching
    else:
        preamble_end_offset = keyword_preamble_end_offset + 200 ######## take few more characters as judge names are written after JUDGEMENT keywords
    truncated_txt = txt[:preamble_end_offset]
    guessed_preamble_end = guess_preamble_end(truncated_txt, preamble_splitting_nlp)

    if guessed_preamble_end==0 :
        preamble_end = keyword_preamble_end_offset
    else:
        preamble_end = guessed_preamble_end

    preamble_txt = txt[:preamble_end]
    title_txt = convert_upper_case_to_title(preamble_txt)
    return title_txt,preamble_end

def get_useful_text_from_indiankanoon_html_tag(ik_tag):
        tag_txt = ''
        for content in ik_tag.contents:
            if isinstance(content, Tag):
                if not (content.get('class') is not None and 'hidden_text' in content['class']):
                    tag_txt = tag_txt + content.text
            else:
                tag_txt = tag_txt + str(content)
        return tag_txt

def get_text_from_indiankanoon_url(url):
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        try:
            webpage = urlopen(req, timeout=10).read()
            page_soup = soup(webpage, "html.parser")

            first_preamble_tag = page_soup.find('pre')
            first_preamble_tag_text = get_useful_text_from_indiankanoon_html_tag(first_preamble_tag)
            preamble_ids=[]
            preamble_text = first_preamble_tag_text
            for next_tag in first_preamble_tag.find_all_next(string=False):
                if next_tag.get('id') is not None and next_tag['id'].startswith('pre_'):
                    preamble_text = preamble_text + get_useful_text_from_indiankanoon_html_tag(next_tag)
                    preamble_ids.append(next_tag.get('id'))
                elif next_tag.get('id') is not None and next_tag['id'].startswith('p_') :
                    break

            judgment_txt_tags = page_soup.find_all(['p', 'blockquote','pre'])
            judgment_txt = ''
            for judgment_txt_tag in judgment_txt_tags:
                if judgment_txt_tag.get('id') in preamble_ids:
                    continue
                tag_txt = ''
                if judgment_txt_tag.get('id') is not None and (judgment_txt_tag['id'].startswith('p_') or
                                                               judgment_txt_tag['id'].startswith('blockquote_') or
                                                               judgment_txt_tag['id'].startswith('pre_')):
                    for content in judgment_txt_tag.contents:
                        if isinstance(content, Tag):
                            if not(content.get('class') is not None and 'hidden_text' in content['class']):

                                tag_txt = tag_txt + content.text
                        else:
                            tag_txt = tag_txt + str(content)


                    tag_txt = re.sub(r'\s+(?!\s*$)', ' ',
                                     tag_txt)  ###### replace the multiple spaces, newlines with space except for the ones at the end.
                    tag_txt = re.sub(r'([.\"\?])\n', r'\1 \n\n',
                                     tag_txt)  ###### add the extra new line for correct sentence breaking in spacy

                    judgment_txt = judgment_txt + tag_txt
            judgment_txt = re.sub(r'\n{2,}', '\n\n', judgment_txt)
            judgment_txt = preamble_text + '\n\n' +judgment_txt

        except:
            judgment_txt = ''

        ###### remove known footer, header patterns
        regex_patterns_to_remove = ['http://www.judis.nic.in','::: (Uploaded on - |Downloaded on -)+ .*?:::']
        for pattern in regex_patterns_to_remove:
            judgment_txt = re.sub(pattern,"",judgment_txt)

        return judgment_txt.strip()

def check_hidden_text_is_invalid(text):
    return True ## Most of the times hiddent text is garbage
    # if not bool(re.match('[a-zA-Z]',"".join(text.split()))):
    #     return True
    # elif bool(re.match('::: (Uploaded on - |Downloaded on -)+ .*?:::',text)):
    #     return True
    # else:
    #     return False
def get_text_from_indiankanoon_url( url):
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})

        try:
            webpage = urlopen(req, timeout=10).read()
            page_soup = soup(webpage, "html.parser")

            judgment_txt_tags = page_soup.find_all(['p', 'blockquote', 'pre'])
            judgment_txt = ''
            for judgment_txt_tag in judgment_txt_tags:
                tag_txt = ''
                if judgment_txt_tag.get('id') is not None and (judgment_txt_tag['id'].startswith('p_') or
                                                               judgment_txt_tag['id'].startswith('blockquote_') or
                                                               judgment_txt_tag['id'].startswith('pre_')):
                    for content in judgment_txt_tag.contents:
                        if isinstance(content, Tag):
                            if content.get('class') is not None and 'hidden_text' in content['class']:
                                if not check_hidden_text_is_invalid(content.text.strip()):
                                    tag_txt = tag_txt + str(content)
                            else:
                                tag_txt = tag_txt + content.text
                        else:
                            tag_txt = tag_txt + str(content)

                    if not judgment_txt_tag['id'].startswith('pre_'):
                        ##### remove unwanted formating except for pre_ tags
                        tag_txt = re.sub(r'\s+(?!\s*$)', ' ',
                                         tag_txt)  ###### replace the multiple spaces, newlines with space except for the ones at the end.
                        tag_txt = re.sub(r'([.\"\?])\n', r'\1 \n\n',
                                         tag_txt)  ###### add the extra new line for correct sentence breaking in spacy
                        tag_txt = re.sub(r'\n{2,}', '\n\n', tag_txt)

                    judgment_txt = judgment_txt + tag_txt

        except:
            judgment_txt = ''

            ###### remove known footer, header patterns
        regex_patterns_to_remove = [{'pattern': 'http://www.judis.nic.in(\s*?\x0c\s*?)?'},
                                    {
                                        'pattern': '(::: Uploaded on - \d\d/\d\d/\d\d\d\d\s+)?::: Downloaded on - .{5,50}:::'},
                                    {'pattern': 'https://www.mhc.tn.gov.in/judis/(\s*?\x0c\s*?)?'},
                                    {
                                        'pattern': 'Signature Not Verified Signed By:.{5,100}Signing Date:\d\d\.\d\d\.\d\d\d\d(.{1,50}Page \d+\s*?! of \d+\s*?!\s*?\d\d:\d\d:\d\d)?',
                                        'flags': re.DOTALL | re.IGNORECASE},
                                    ]
        for pattern_dict in regex_patterns_to_remove:
            if pattern_dict.get('flags') is not None:
                judgment_txt = re.sub(pattern_dict['pattern'], "", judgment_txt, flags=pattern_dict['flags'])
            else:
                judgment_txt = re.sub(pattern_dict['pattern'], "", judgment_txt)

        return judgment_txt.strip()

def get_sentence_docs(doc_judgment,nlp_judgment):
    sentences=[sent.text for sent in doc_judgment.sents]
    docs=[]
    for doc in nlp_judgment.pipe(sentences):
        docs.append(doc)
    combined_docs=spacy.tokens.Doc.from_docs(docs)
    return combined_docs

def get_json_from_spacy_doc(doc):
    import uuid
    uid = uuid.uuid4()
    id = "LegalNER_" + str(uid.hex)
    output = {'id': id, 'annotations': [{'result': []}], 'data': {'text': doc.text}}
    for ent in doc.ents:
        import uuid
        uid = uuid.uuid4()
        output['annotations'][0]['result'].append(copy.deepcopy({
                    "value": {
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "text": ent.text,
                        "labels": [ent.label_],
                        "id": uid.hex
                    }
                }))
    return output        
         
