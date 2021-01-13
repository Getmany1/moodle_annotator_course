import pandas as pd
import re

def get_ratings(csv_file):
    """
    csv_file: csv file from quiz -> responses -> download .csv
    """
    rating_list = []
    df = pd.read_csv(csv_file)
    #df.columns # list column names
    
    # Iterate over rows. Each row corresponds to an attempt in Moodle rater quiz
    # (in case of multiple raters in the same bundle one row corresponds to the
    # grades of one rater).
    for idx, _ in df.iterrows():
        rater = df['Sukunimi'][idx]
        for column in df:
            # extract student id and task number
            if 'Kysymys' in column:
                data = df[column][idx].split('\n\n\t\t')
                student_id = data[0].split(':')[1][1:]
                task = data[1].split(':')[1][1:]
            # extract answers
            elif 'Vastaus' in column:
                answers = []
                data = df[column][idx].split(';')
                # merge the part 'Sujuvuus' if needed (';' in rubrics)
                if 'sujuva' in data[3]:
                    data[3:5] = [';'.join(data[3:5])]
                # The 'data' here is supposed to consist of 13 parts. If there are
                # more than 13 elements in the list, then rater has used ';' symbol
                # in comments.
                # Merge comment into a single element.
                if len(data) > 13:
                    data[12:] =[';'.join(data[12:])]
                for i, osa in enumerate(data):
                    data[i] = osa.split(':')
                    
                    ## Remember to check this piece of code after you change the quiz template
                    # Odd elements are CEFR level, comments or redundant empty elements
                    if int(data[i][0].split(' ')[-1])%2 == 1:
                        # First element = CEFR level
                        if i == 0:
                            answers += [data[i][1][1:]]
                        # Last element = comments
                        elif i == len(data)-1:
                            answers += [data[i][1]]
                        # The rest of odd elements are empty.
                        else:
                            continue
                    # Even elements are grades. Some of them may be empty (= grade missing)    
                    else:
                        # Empty answer => add '_'
                        if data[i][1] == ' ':
                            answers += '_'
                        # Non-empty answer => extract grade
                        else:
                            answers += re.findall(r"\((\d+)\)", data[i][1])[0]
                        
                # Add the extracted data to the list
                rating_list += [[rater, student_id, task] + answers]
                
    return rating_list