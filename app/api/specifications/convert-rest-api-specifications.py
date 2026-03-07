import os
import json

os.system('clear')
project_dir = os.path.abspath(os.path.dirname(__file__))
file_path = os.path.join(project_dir, "restapiV2.json")

def generateCategoryListOfTuples(filePath):
    with open(filePath, 'r') as file:
        data = json.load(file)

        path_list = data["paths"].keys()
        category_list = []

        for path in path_list:
            split_list = path.split("/")
            if len(split_list) > 1:
                category = "/".join(split_list[:2])
            else:
                category = path
            
            category_tuple = (category, category[1:].title())
            if not category_tuple in category_list:
                category_list.append(category_tuple)
        return category_list

def generatePathListOfTuples(filePath):
    with open(filePath, 'r') as file:
        data = json.load(file)

        path_list = data["paths"].keys()
        path_list_tuple = []
        for path in path_list:
            path_tuple = (path, path)
            path_list_tuple.append(path_tuple)
        return path_list_tuple


category_list = generateCategoryListOfTuples(file_path)
print(category_list)


# path_list_tuple = generatePathListOfTuples(file_path)
# print(path_list_tuple)