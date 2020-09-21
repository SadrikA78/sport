#генерация номеров 
import random as r

def generate_key():
    random_string = ''
    random_str_seq = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for i in range(2):
        random_string += str(random_str_seq[r.randint(0, len(random_str_seq) - 1)])
    random_string += '-'
    random_str_seq = "0123456789"
    for i in range(5):
        random_string += str(random_str_seq[r.randint(0, len(random_str_seq) - 1)])
    return(random_string)