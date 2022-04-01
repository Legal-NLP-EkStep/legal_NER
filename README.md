# legal_NER
## Why Seperate NER for Indian Legal Texts?
Legal Named Entity Recognition (L-NER): Named Entities Recognition is commonly studied problem in Natural Language Processing and many pre-trained models are publicly available. However legal documents have peculiar named entities like names of petitioner, respondent, court, statute, provision, precedents,  etc. These entity types are not recognized by standard Named Entity Recognizer like spacy. Hence there is a need to develop a Legal NER system.
## What Legal Entities are covered?
| NER             | Group    | Description                                                                                                                                                                                                                                |
| --------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Court           | ORG      | Name of the courts (supreme , high court, district etc.) mentioned in text.                                 |
| Police Station  | ORG      | Police Station mentioned anywhere in text                                                                                                                                                                                                  |
| Organization    | ORG      | Name of organizations mentioned in text apart from court & police stations. E.g. Banks, PSU, private companies                                                                                                                           |
| Statute         | LAW      | Name of the act or law under which case is filed                                                                                                                                                                                           |
| Provision       | LAW      | Sections, articles or rules under the statute                                                                                                                                                                                              |
| Precedent       | CASE\_ID | Higher Court cases referred in the judgment                                                                                                                            |
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

## Extracting entities from your custom text
```python
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
## How Legal NER works?
legal NER breaks the judgment into 2 parts viz. preamble and main text. 
Legal NER is based on spacy models and adds 

## Customizing rules for best results on your data
