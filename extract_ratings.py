import pandas as pd
import re
import glob, os

def get_rating_list(csv_file):
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
                        # Empty answer => add 9999
                        if data[i][1] == ' ':
                            answers += [9999]
                        # Non-empty answer => extract grade
                        else:
                            answers += [int(re.findall(r"\((\d+)\)", data[i][1])[0])]
                        
                # Add the extracted data to the list
                rating_list += [[student_id, task, rater] + answers]
                
    return rating_list

def main():
    rating_list = [] # list of lists of ratings
    columns = ['Opiskelija',
               'Tehtävä',
               'Arvioija',
               'Arvio taitotasosta',
               'Tehtävän suorittaminen',
               'Sujuvuus',
               'Ääntäminen',
               'Ilmaisun laajuus tehtävänantoon nähden',
               'Sanaston ja kieliopin tarkkuus',
               'Varmuus arviosta',
               'Kommentteja'] # columns in output table. ATTENTION: the order
                                # should be the same as in rating_list
                                # from get_rating_list()
    # The CSV files with ratings should be located in the same folder with this script
    for file in glob.glob("*.csv"):
        rating_list += get_rating_list(file)
        
    # Sort ratings by 1. student ID, 2. task ID, 3. rater ID
    rating_list.sort(key=lambda x: (x[0], x[1], x[2]))
    
    # Convert to a dataframe
    newtable = pd.DataFrame(rating_list, columns=columns)
    
    # Save table in .csv and .xlsx formats
    newtable.to_csv('ratings_2021.csv', encoding='utf-8-sig', index=False)
    newtable.to_excel('ratings_2021.xlsx', encoding='utf-8-sig', index=False)
    
main()