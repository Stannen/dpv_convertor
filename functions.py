import numpy as np 
import os 
import csv 
import yaml


def dirOperator(path, make=True, returnList=False):
    ''' make=False (return True if path is correct else False) 
        make=True (if folder is not avaible make a new folder 
        returnList=True and Make=False (return list of all the folders)'''        
    
    if make:
        splitedPath = path.split('/')
        scanPath = '' 

        for i in range(0, len(splitedPath)):
            if i == 0: scanPath = splitedPath[i]               
            else: scanPath += f'/{splitedPath[i]}'
                
            if not os.path.isdir(scanPath):
                os.mkdir(scanPath)  

    elif returnList:
        if os.path.isdir(path):
            return os.listdir(path) 
        else:
            return [] 
    else:
        return os.path.isdir(path) 
    

def SeriesOperator(filePath, series=None, encoding='utf-8', delimiter=','): 
    ''' series=None (load series)
        series=not None (save series)'''

    if not filePath.count('/') > 0 or not filePath.count('.') == 1:
        return None 
        
    path, extension = filePath.split('.')
    fileName = path.split('/')[-1]
    path = path.replace(f'/{fileName}', '')

    if extension == 'csv' or extension == 'npy' or extension == 'xlsx':
        if series == None:   
            if not os.path.isfile(filePath):     
                return False
            returnData = None 

            if extension == 'csv' or extension == 'xlsx':
                returnData = []
               
                with open(filePath,'r', encoding=encoding) as file:
                    #csvFile = None 

                    #if extension == 'csv':
                    csvFile = csv.reader(file, delimiter=delimiter)
                    #else:
                        #csvFile = csv.reader(file, delimiter='"')
                   
                    for row in csvFile:
                        returnData.append([veld.strip() for veld in row])                       
                
            elif extension == 'npy':
                returnData = np.load(filePath, allow_pickle=True)
                returnData = np.array(returnData)
                
            return returnData

        else:
            if not os.path.isdir(path):
                dirOperator(path)
                print('path bestaat niet')           
                     
            if extension == 'csv':    
                with open(filePath, 'w', newline='', encoding=encoding) as file:      
                    csvFile = csv.writer(file, quoting=csv.QUOTE_ALL)
                    
                    for row in series:   
                        try:
                            csvFile.writerow([veld.strip() for veld in row])       
                        except:
                            csvFile.writerow(row)       
                            

            elif extension == 'npy':
                np.save(filePath, np.array(series, dtype=object), allow_pickle=True)               
                    
            if not os.path.isfile(filePath):
                print('file is niet aangemaakt')
                return None  


def fileOperator(path, returnList=False, deleteExtension=True):
    ''' returnList=False (check if file exist)
        returnList=True (return list of files)'''

    if returnList:
        if os.path.exists(path):
            returnData = [] 
            for root, dirs, files in os.walk(path):   
                if not path == root:
                    continue                
                
                if deleteExtension:
                    for select in files:
                        returnData.append(select.split('.')[0])
                else:
                    for select in files:     
                        returnData.append(select) 
            return returnData

    else:
        return os.path.isfile(path)


def yamlOperator(fileName, path=None, data=None): 
    ''' series=None (load series)
        series=not None (save series)
        
        extension=csv 
        extension=npy'''

    if fileName.count('.') == 0:
        fileName += '.yaml'

    if path is None:
        filePath = fileName

    else:
        filePath = f'{path}/{fileName}'

    if data == None:
        print(filePath)
        if not os.path.isfile(filePath):
            return None 
        
        with open(filePath, 'r') as file:
            return yaml.safe_load(file)  

    else:
        with open(filePath, 'w') as file:
            yaml.dump(data, file)