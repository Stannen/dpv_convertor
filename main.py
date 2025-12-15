import csv
import sys
from pathlib import Path
import ctypes
from datetime import datetime
import logging
import os 
from jinja2 import Template
from copy import deepcopy
import itertools
import math

import functions as fnc  
from dataclasses import dataclass, field

class Convertor:
    def __init__(self):

        @dataclass
        class Dpv:
            categorys: list[str] = field(default_factory=list)
            nozzle1: str = None 
            nozzle2: str = None       
            
            usedFootprints: list[str] = field(default_factory=list)
                    
            footprintGroup: list[str] = None
            rawData: list[any] = field(default_factory=list)

            feeders: list[any] = field(default_factory=list)
            fiducials: list[any] = field(default_factory=list)
            placements: list[any] = field(default_factory=list)

        @dataclass
        class Components:
            category: str = None
            columns:  list[any] = None 
            components: list[any] = None
        
        @dataclass
        class Feeders():
            category: str = None
            componentId: int = None

            stationId: int = None
            minStationId: int = None
            maxStationId: int = None
            tapeSize: int = None
            head: int = None

            speed: int = 0 
            feedRate: int = 0
            pullSpeed: int = 0 

            height: int = 0

    
        self.Dpv = Dpv
        self.Components = Components
        self.Feeders = Feeders
     
        logging.basicConfig(filename='log.log', level=logging.DEBUG,
        format='%(asctime)s %(levelname)s:%(message)s')

        self.config = fnc.yamlOperator('config.yaml')

        self.defaultFeeders = list() #device 
        self.components = dict()   #category
        self.loadComponents()


    def findFeeder(self, feeders, category, componentId):
        for feeder in feeders:
            if feeder.category == category and feeder.componentId == componentId:
                return feeders[feeders.index(feeder)]
        return None


    def getTapeSize(self, tapeSize):
        tape = ''
        for char in tapeSize:
            if char.isdigit():
                tape += char
                   
        return int(tape)


    def loadComponents(self):
        path = 'components'

        categoryFiles = fnc.fileOperator(path, True, False)    

        for categoryFile in categoryFiles:
            category = categoryFile.split('.')[0]
            data = fnc.SeriesOperator(f'{path}/{categoryFile}')

            components = self.Components()
            components.columns = [item.lower() for item in data[0]]
            components.components = data[1:]

            for component in components.components:
                defaultFeeder = component[components.columns.index('default feeder')]

                if defaultFeeder == '':
                    continue

                componentId = components.components.index(component)

                if self.findFeeder(self.defaultFeeders, category, componentId) is None:
                    feeder = self.Feeders()
                    feeder.category = category
                    feeder.componentId = componentId
                    feeder.stationId = int(defaultFeeder)
                    feeder.tapeSize = self.getTapeSize(component[components.columns.index('tape size')])

                    f = self.config['feederMap'][feeder.tapeSize]
                    for key in f:
                        if not hasattr(feeder, key):
                            continue

                        feeder.__dict__[key] = f[key]                  
                    self.defaultFeeders.append(feeder) 

                else:
                    self.log(f'Defauld feeder:{defaultFeeder} already exist', 'error')

            components.category = category
            self.components[category] = components


    def saveComponents(self):
        path = 'components'

        for category in self.components:
            components = self.components[components]
            fnc.SeriesOperator(f'{path}/{category.category}.csv', series=[components.columns, components.components])


    def getInput(self, additionText=None, additionList=None, onlyPrint=False):  
            command = None 
            while True:
                
                if not additionList == None:
                    if len(additionList) == 0:
                        print('No item in list')
                    else:
                        title = 'Options'
                        if not additionText == None:
                            title = additionText
                    
                        print(f'--{title}--')
                        for i in range(len(additionList)):
                            print(f'[{i}]', additionList[i]) 
                        print('--end--')
                        
                elif not additionText == None:
                    print(additionText)
                
                if not onlyPrint:
                    command = input('cp>').lower()  
                
                if additionList == None or onlyPrint:  
                    break 
                else:

                    if not command.isdigit() or int(command) > len(additionList) -1:
                        continue

                    command = additionList[int(command)]
                    break
                                     
            return command     


    def run(self):
        while True:
            command = self.getInput(additionList=('help','convert','add','remove','close', 'find')) 

            if command == 'help':
                print(''' \n
                         convert --> Convert the file to dpv \n
                         add --> Add a new component \n 
                         remove --> Remove a existing component \n
                         close --> Close this application \n
                         find --> find fo a component exist ''')
                
            elif command == 'convert':
                self.convert() 

            elif command == 'add':
                self.addComponent()

            elif command == 'remove':
                self.removeComponent()

            elif command == 'close':
                return 
            
            elif command == 'find':
                componentsFound = []
                componentItems = [] 

                while True:
                    for i in range(len(componentsFound)):
                        print(f'{componentsFound[i]}')
                        
                    newItem = self.getInput('add component item')

                    if newItem == 'exit':
                        break 

                    componentItems.append(newItem)
                    componentsFound.clear()

                    for category in self.components:
                        components = self.components[category]

                        for component in components.components:

                            allItemsFound = True 
                            for item in componentItems:
                                itemFound = False 
                                for rowItem in component:
                                    if rowItem.lower().count(item) > 0:
                                        itemFound = True 

                                if not itemFound:
                                    allItemsFound = False 

                            if allItemsFound:
                                
                                componentsFound.append(component)

                    if len(componentsFound) == 0:
                        print('No components found')
                        break 
      

    def convert(self):
        dpvFiles, calib_points = [], []    

        def prepareEasyedaData(path):
            data = fnc.SeriesOperator(filePath, encoding='utf-16', delimiter='\t')
            columns = [item.lower() for item in data[0]] 
            data = data[1:]

            for column in self.config['easyedaRequiredColumns']:
                if not column.lower() in columns:
                    self.log(f'There is missing the following column in the easyeda export: {column}')


            xIndex = columns.index('x')
            yIndex = columns.index('y')
            rotationIndex = columns.index('rotation')

            for i in range(len(data)):
                data[i][xIndex] = float(data[i][xIndex].replace('mm', ''))
                data[i][yIndex] = float(data[i][yIndex].replace('mm', ''))
                data[i][rotationIndex] = int(data[i][rotationIndex])

            return data, columns


        def findComponent(easyedaRow, easyedaColumns):
            for category in self.components:
                components = self.components[category]

                for component in components.components:
                    exist = True 
                    for column in easyedaColumns:
                        if components.columns.count(column) > 0:
                            if not easyedaRow[easyedaColumns.index(column)].lower().count(component[components.columns.index(column)].lower()) == 1:
                                exist = False

                    if exist:
                        return components, components.components.index(component)                         
            return None, None


        def findNozzleAndFootprint(componentClass):
            nozzleSelected, footprintSelected = None, None  
            for nozzle in dict(self.config['nozzleMap']):
                footprints = self.config['nozzleMap'][nozzle]

                for footprint in footprints:
                    if componentClass.components[componentId][componentClass.columns.index('footprint')].lower().count(footprint.lower()) == 1:
                        return nozzle, footprint
            return None, None


        def findFootprintGroup(footprintSelected):
            for group in self.config['preferenceGroups']:
                if group.count(footprintSelected) == 1:
                    return group 
            return None 


        def get_dpv_file(nozzleSelected, footprintSelected, componentId, componentClass):
            groupAvailable = findFootprintGroup(footprintSelected)            

            tapeSize = self.getTapeSize(componentClass.components[componentId][componentClass.columns.index('tape size')])
            minStationId = self.config['feederMap'][tapeSize]['minStationId']
            maxStationId = self.config['feederMap'][tapeSize]['maxStationId']

            for dpvFile in dpvFiles:
                count = 0
                for feeder in dpvFile.feeders:
                    if feeder.tapeSize == tapeSize:
                        count += 1

                if count >= maxStationId - minStationId:
                    continue            
                
                if groupAvailable is not None:
                    if dpvFile.footprintGroup is not None: 
                        if dpvFile.footprintGroup.count(footprintSelected) == 1:
                            if dpvFile.nozzle1 == nozzleSelected or dpvFile.nozzle2 == nozzleSelected or dpvFile.nozzle2 is None:
                                return dpvFiles[dpvFiles.index(dpvFile)]

                else:
                    if dpvFile.nozzle1 == nozzleSelected or dpvFile.nozzle2 == nozzleSelected or dpvFile.nozzle2 is None:
                        return dpvFiles[dpvFiles.index(dpvFile)]
            return None
                  

        def addCalibPoint(easyedaRow, easyedaColumns):
            calib_point = {}

            for key in self.config['calib_point']['columns']:
                useDefauld = False
                if self.config['calib_point']['default'].get(key) is not None:
                    calib_point[key] = self.config['calib_point']['default'][key]
                    useDefauld = True
                        
                if key == 'note':
                    calib_point[key] = f"{easyedaRow[easyedaColumns.index('designator')]}: {easyedaRow[easyedaColumns.index('footprint')]}"

                elif easyedaColumns.count(key) > 0:
                    calib_point[key] = easyedaRow[easyedaColumns.index(key)]

                else:
                    if not useDefauld:
                        self.log(f'Key: {key} not found in easyeda export', 'error')

            return calib_point


        def distance(p1, p2):
            dx = float(p1['x']) - float(p2['x'])
            dy = float(p1['y']) - float(p2['y'])
            return math.sqrt(dx**2 + dy**2)


        def spread_score(points):
            # minimale afstand als maat voor spreiding
            dists = [distance(a, b) for a, b in itertools.combinations(points, 2)]
            return sum(dists) / len(dists) if dists else 0


        def best_spread(points, n):
            """
            Kies n punten uit de lijst die de maximale spreiding hebben.
            Brute-force combinaties voor kleine n, greedy voor grotere n.
            """
            if n <= 2:
                # gewoon de 2 verste punten
                return max(itertools.combinations(points, n), key=spread_score)

            # brute-force voor kleine sets
            if len(points) < 20:  
                return max(itertools.combinations(points, n), key=spread_score)

            # greedy benadering voor grotere sets
            chosen = [points[0]]
            while len(chosen) < n:
                candidates = [p for p in points if p not in chosen]
                scores = [(spread_score(chosen + [c]), c) for c in candidates]
                best = max(scores, key=lambda x: x[0])[1]
                chosen.append(best)
            return chosen


        fileName =  input('Enter the file name of a csv file you want to convert to dpv->')
        filePath = f"{self.config['getPath']}/{fileName}.csv"
         
        easyedaData, easyedaColumns = prepareEasyedaData(filePath)

        notFoundComponens, notComponens = [], []  
        
        for easyedaRow in easyedaData:        
            components, componentId = findComponent(easyedaRow, easyedaColumns)      
            nozzleSelected, footprintSelected = None, None 

            if components is not None:
                nozzleSelected, footprintSelected = findNozzleAndFootprint(components)

            if nozzleSelected is None:
                found = False 
                for nozzle in dict(self.config['nozzleMap']):
                    footprints = self.config['nozzleMap'][nozzle]

                    for footprint in footprints:
                        if easyedaRow[easyedaColumns.index('footprint')].lower().count(footprint) > 0:
                            found = True 

                if found:
                    notFoundComponens.append(easyedaRow)
                else:
                    notComponens.append(easyedaRow)
                continue         
              
            calib_points.append(addCalibPoint(easyedaRow, easyedaColumns))
                   
            dpvFile = get_dpv_file(nozzleSelected, footprintSelected, componentId, components)
            
            if dpvFile is None:
                dpvFile = self.Dpv()
                             
                dpvFile.footprintGroup = findFootprintGroup(footprintSelected)
                dpvFile.nozzle1        = nozzleSelected
       
                dpvFiles.append(dpvFile)

            else:
                if dpvFile.nozzle1 != nozzleSelected and dpvFile.nozzle2 is None:
                    dpvFile.nozzle2 = nozzleSelected

            if dpvFile.categorys.count(components.category) == 0:
                dpvFile.categorys.append(components.category)

            feeder = self.findFeeder(dpvFile.feeders, components.category, componentId)

            if feeder is None:           
                defaultFeeder = self.findFeeder(self.defaultFeeders, components.category, componentId)

                if defaultFeeder is None:
                    feeder = self.Feeders()
                    feeder.category = components.category
                    feeder.componentId = componentId
                    feeder.tapeSize = self.getTapeSize(components.components[componentId][components.columns.index('tape size')])

                    f = self.config['feederMap'][feeder.tapeSize]
                    for key in f:
                        if not hasattr(feeder, key):
                            continue
                        feeder.__dict__[key] = f[key]

                    defauldStationids = [] 
                    for select in self.defaultFeeders:
                        if select.tapeSize == feeder.tapeSize:
                            defauldStationids.append(select.stationId)
                    
                    usedIds = []
                    for select in dpvFile.feeders:
                        if select.tapeSize == feeder.tapeSize:
                            usedIds.append(select.stationId)

                    for stationId in range(feeder.minStationId, feeder.maxStationId):
                        if usedIds.count(stationId) == 0 and defauldStationids.count(stationId) == 0:
                            feeder.stationId = stationId
                            break 

                        elif usedIds.count(stationId) == 0:
                            feeder.stationId = stationId

                    dpvFile.feeders.append(feeder)

                else:
                    dpvFile.feeders.append(deepcopy(defaultFeeder))
                    
            if dpvFile.usedFootprints.count(footprintSelected) == 0:
                dpvFile.usedFootprints.append(footprintSelected)

            dpvFile.rawData.append([easyedaRow, components.category, componentId, nozzleSelected])

        print('-- Componens not available --')
        for item in notFoundComponens:
            self.log(f'Not found {item}', 'info')

        for item in notComponens:
            self.log(f'No smd footprint {item} ', 'info')


        if self.config['deleteSavedFiles']:
            files = fnc.fileOperator(self.config['savePath'], True, False)
            
            for file in files:
                try:
                    os.remove(self.config['savePath'] + '/' + file)
                except Exception as e:
                    self.log(f'Could not delete file: {file}. Error: {e}', 'info')


        calib_points = best_spread(calib_points, 3)

        for dpvFile in dpvFiles:
            stations, ecomponents = [], []

            for feeder in dpvFile.feeders:
                station = {}
                
                component = self.components[feeder.category].components[feeder.componentId]
                componentColumns = self.components[feeder.category].columns

                for key in self.config['station']['columns']:
                    useDefauld = False 

                    if self.config['station']['default'].get(key) is not None:
                        station[key] = self.config['station']['default'][key]
                        useDefauld = True

                    if key == 'status':
                        skip = 0
                        if self.config['placeComponent']:
                            skip += 0b001
                        if self.config['checkVacuum']:
                            skip += 0b010
                        if self.config['useVision']:
                            skip += 0b100
                        station[key] = skip

                    elif key == 'note':
                        station[key] = component[componentColumns.index('footprint')]

                    elif hasattr(feeder, key):
                        station[key] = feeder.__dict__[key]

                    elif componentColumns.count(key) > 0:
                        station[key] = component[componentColumns.index(key)]

                    else:
                        if not useDefauld:
                            self.log(f'Key: {key} not found in feeder or component export', 'error')

                stations.append(station)


            for easyedaRow, category, componentId, nozzleSelected in dpvFile.rawData:
                components = self.components[category]
                ecomponent = {}

                feeder = self.findFeeder(dpvFile.feeders, category, componentId)
                
                for key in self.config['ecomponent']['columns']:

                    useDefauld = False
                    if self.config['ecomponent']['default'].get(key) is not None:
                        ecomponent[key] = self.config['ecomponent']['default'][key]
                        useDefauld = True

                    if key == 'head':
                        head = 1 if nozzleSelected == dpvFile.nozzle1 else 2
                        ecomponent[key] = head   

                    elif key == 'rotation':
                        rotation = easyedaRow[easyedaColumns.index("rotation")]
                        rotation -= 90
                        ecomponent[key] = ((rotation+180)%360)-180
                    
                    elif key == 'explain':
                        ecomponent[key] = easyedaRow[easyedaColumns.index("designator")]

                    elif key == 'note':
                        ecomponent[key] = {easyedaRow[easyedaColumns.index("designator")]}

                    elif key == 'skip':
                        skip = 0
                        if self.config['placeComponent']:
                            skip += 0b001
                        if self.config['checkVacuum']:
                            skip += 0b010
                        if self.config['useVision']:
                            skip += 0b100
                        ecomponent[key] = skip

                    elif easyedaColumns.count(key) > 0:
                        ecomponent[key] = easyedaRow[easyedaColumns.index(key)]

                    elif feeder is not None and hasattr(feeder, key):
                        ecomponent[key] = feeder.__dict__[key]

                    else:
                        if not useDefauld:
                            self.log(f'Key: {key} not found in easyeda export', 'error')
                
                ecomponents.append(ecomponent)

            now = datetime.now()
            
            fileName = f'H1_{dpvFile.nozzle1}_H2_{dpvFile.nozzle2}_{"_".join(dpvFile.categorys)}'

            header = {
                "file": fileName,
                "pcbfile": os.path.basename(filePath),
                "date": "{:02d}/{:02d}/{:02d}".format(now.year, now.month, now.day),
                "time": "{:02d}:{:02d}:{:02d}".format(now.hour, now.minute, now.second),
                "paneltype": 0,
            }


            try:
                with open(f"{self.config['savePath']}/{fileName}.dpv", 'w') as dpv:
                    with open('template.dpv.j2', 'r') as f:
                        template = Template(f.read())
                    dpv.write(template.render(header=header, stations=stations, ecomponents=ecomponents, calib_points=calib_points))
                print(f'File: {fileName} saved')

            except Exception as e:
                self.log(f'Could not save dpv file. Error: {e}', 'info')


    def addComponent(self):
        categorys = [] 
        
        for componentClass in self.components:
            categorys.append(componentClass.category)

        category = self.getInput(additionList=categorys)

        componentClass = self.components[categorys.index(category)]

        row = [] 
        for item in componentClass.columns:
            row.append(self.getInput(f'Enter {item}'))

        componentClass.data.append(row)
        self.saveComponents()         


    def removeComponent(self):
        categorys = [] 
        
        for componentClass in self.components:
            categorys.append(componentClass.category)

        category = self.getInput(additionList=categorys)

        componentClass = self.components[categorys.index(category)]
        for index, row in enumerate(componentClass.data):
            print(f'{index}: {row}')
        
        rowIndex = self.getInput('Enter the index of the component you want to remove')
        
        if rowIndex.isdigit():
            componentClass.data.pop(int(rowIndex))
            self.saveComponents()


    def log(self, msg, level='error'): 
        levels = ['error', 'info']

        if levels.count(level) != 1:
            logging.error(f" -- {datetime.now()} -- level: {level} don't exist")
            return 

        logging.__dict__[level](f' -- {datetime.now()} -- {msg}')
        print(f'{level}: {msg}')

        if level == 'error':
            sys.exit()
            

def is_admin():
    if os.name == 'nt':  # Windows
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:  # Linux/WSL
        return os.geteuid() == 0

if is_admin() or True:
    convertor = Convertor()
    convertor.run()
else:
    print("Dit script heeft geen administrator/root-rechten.")
