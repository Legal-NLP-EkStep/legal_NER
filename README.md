# legal_NER
## Why Seperate NER for Indian Legal Texts?
Named Entities Recognition is commonly studied problem in Natural Language Processing and many pre-trained models are publicly available. However legal documents have peculiar named entities like names of petitioner, respondent, court, statute, provision, precedents,  etc. These entity types are not recognized by standard Named Entity Recognizer like spacy. Hence there is a need to develop a Legal NER model. But ther are no publicly available annotated datasets for this task. In order to help the data annotation process, we have created this rule based approach on top of pretrained spacy models. The NER tags created could be inspected by humans to correct which eventually could be used to train an AI model.
## Which Legal Entities are covered?
This code can extract following named entities from Indian Court judgments.
| NER             | Group    | Description                                                                                                                                                                                                                                |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Court           | ORG      | Name of the courts (supreme , high court, district etc.) mentioned in text.                           
| Geopolitical Entity  | ORG      | Geopolitical Entity  
| Organization    | ORG      | Name of organizations mentioned in text apart from court & police stations. E.g. Banks, PSU, private companies 
| Date            | DATE     | Any date mentioned in the judgment
| Statute         | LAW      | Name of the act or law under which case is filed                                                                                                                                                                                           |
| Provision       | LAW      | Sections, articles or rules under the statute                                                                                                                                                                                              |
| Precedent       | CASE\_ID | Past Court cases referred in the judgment as precedent                                                                                                                            |
| Case number     | CASE\_ID | Other Case number mentioned in the current judgment                                                                                                                                                                   |
| Petitioner Name | PERSON   | Name of Appellant/ Petitioner in current judgment. The names could be multiple. Only names should be matched and suffixes like Dr.,Mr., Etc. should be excluded. The references to Appellants like appellant no.1 should also be excluded. |
| Respondent Name | PERSON   | Name of Respondent in current judgment                                                                                                                                                                                                     |
| Judge Name      | PERSON   | Name of judge in current case                                                                                                                                                                                                              |
| Lawyer Name     | PERSON   | Name of Lawyers                                                                                                                                                                                                                            |
| Witness Name    | PERSON   | Name of witnesses in current judgment                                                                                                                                                                                                      |
| other person    | PERSON   | Names of other people that don't belong to any other categories above       

## Installation
1. Clone the git repo
2. Create a new virtual environment & activate it

```
python3 -m venv /path/to/new/virtual/environment
```

```
source  /path/to/new/virtual/environment/bin/activate
```

4. Install the required packages
```
cd legal_NER
```

```
pip install -r requirements.txt
```

5. Download spacy models

```
python -m spacy download en_core_web_trf
```

```
python -m spacy download en_core_web_sm
```

## Extracting entities from input court judgment text
Please refer to legal_ner.py for extracting entities from custom text.
```python
    from legal_ner import create_spacy_pipelines,extract_entities_from_judgment_text
    from data_preparation import get_text_from_indiankanoon_url
    ############## Get judgment text from indiankanoon or paste your own text 
    indiankanoon_url = 'https://indiankanoon.org/doc/542273/'
    txt = get_text_from_indiankanoon_url(indiankanoon_url) ######## or txt ='paste your judgment text'

    ######## create spacy pipelines needed for preamble & main text
    nlp_preamble,nlp_judgment = create_spacy_pipelines()

    ########## Extract Entities
    combined_doc = extract_entities_from_judgment_text(txt,nlp_judgment,nlp_preamble)

    ########### show the entities
    extracted_ent_labels = list(set([i.label_ for i in combined_doc.ents]))
    colors = {'COURT':"#bbabf2",'PETITIONER': "#f570ea", "RESPONDENT": "#cdee81",'JUDGE':"#fdd8a5","LAWYER":"#f9d380",
              'WITNESS':"violet","STATUTE":"#faea99","PROVISION":"yellow",'CASE_NUMBER':"#fbb1cf","PRECEDENT":"#fad6d6",
              'POLICE_STATION':"#b1ecf7",'OTHER_ORG':"#b0f6a2"}
    options = {"ents": extracted_ent_labels, "colors": colors}

    displacy.serve(combined_doc, style='ent',port=8080,options=options)

```
The output will look like below
![Example NER output](NER_example.png)

## How does Legal NER work?
Legal NER uses spacy NER models and add some rules on top of them. Judgment is broken into 2 parts viz. preamble and judgment text.
### Entities from Preamble
Preamble of judgment contains formatted metadata like names of parties, judges, lawyers,date, court etc. We extract following entities from preamble: Court,Petitioner Name, Respondent Name, Judge Name, Lawyer Name.
Spacy pipeline for preamble is lightweight en_core_web_sm model with custom sentencizer which splits sentences on new lines and does Part of Speech tagging. The proper nouns in the preamble are extracted and are assigned entities based on the rules. The rules are mainly based on the vicinity of the proper nouns to keywords for each entity. E.g. proper noun with word "petitioner" in same sentence is likely to be the name of petitioner. Please refer to preamble_pipeline.py for more details on the rules.

### Entities from judgment  text
The text following preamble till the end of the judgment is the main text. We extract following entities from judgment main text: Court,Petitioner Name, Respondent Name, organization, statute, provision, precedent,case_id, witness name, other person.
Spacy pipeline for the main text is en_core_web_trf model and uses built-in named entity recognizer. The entities extracted from text are futher refined based on the rules. E.g. PERSON followed by pattern (PW1) is likely to be the name of the witness. 
Please refere to judgment_text_pipeline.py for more details on the rules.

## Customizing rules for best results on your data
The rules are written based on the observations from typrical judgments. So it may miss some entities from text. The accuracy of the legal NER is dependent on the accuracy of the spacy pipelines. It is observed that many entities in preamble are missed because the names are not identified as proper nouns. This is because the preamble sentences are not proper English sentences. As next steps OpenNyAI would collect human annotated data for NER and we expect that these models would give much better performance. Till then you can customize the rules as per your data to make this better.

## Acknowledgements
This work is part of [OpenNyAI](https://opennyai.org/) mission which is funded by [EkStep](https://ekstep.org/) and [Agami](https://agami.in/). 
