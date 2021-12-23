import itertools
import random
import operator
ids = ["111111111", "222222222"]


class DroneAgent:
    def __init__(self, initial):
        self.map= initial['map']
        self.drones= initial['drones']
        self.dronesName= set(self.drones.keys())
        self.packages= initial['packages']
        self.clients= initial['clients']
        self.turnsToGo = initial['turns to go']
        self.factor=1
        self.actionsCalculted=dict()
        self.distanceBetweenDroneAndPackage=dict()
        self.clientsMovementsProbabilitiesCalculated= dict()
        self.packagesClientsWant = set()
        for client, value in self.clients.items():
            for packagesClientWant in (set(value['packages'])):
                self.packagesClientsWant.add(packagesClientWant)

    def act(self, state):
        q=[]
        maxValueFound= 0
        bestFirstActAFound=''
        firstActions = self.getAllActions(state['drones'],state['packages'],state['clients'])
        for action in firstActions:
            droneResult, packageResult = self.getResultForAction(state['drones'],state['packages'], action)
            newClientsLocation = self.getNewClientsLocation(state['clients'])
            newValue = self.getImmediateReward(packageResult, droneResult, state['clients'])
            if newValue >= maxValueFound:
                maxValueFound = newValue
                bestFirstActAFound = action
            q.append((droneResult,packageResult,newClientsLocation, newValue, action))
        time=1
        while time< state['turns to go']:
            newQ=[]
            while q:
                current= q.pop()
                droneState= current[0]
                packageState= current[1]
                clientsState = current[2]
                currentValue= current[3]
                firstAct= current[4]
                newClientsLocation= self.getNewClientsLocation(clientsState)
                immidiateReward = self.getImmediateReward(packageState, droneState, newClientsLocation)
                if immidiateReward:
                    prob= self.findProbabilty(clientsState,newClientsLocation)
                else:
                    prob=0
                actions= self.getAllActions(droneState,packageState,newClientsLocation)
                bestActions= self.getBestActionsByHeurisitic(droneState,packageState,newClientsLocation,actions)
                droneResult, packageResult= self.getResultForAction(droneState,packageState,bestActions)
                newValue= currentValue+ self.factor*(immidiateReward*prob)
                if newValue >= maxValueFound:
                    maxValueFound = newValue
                    bestFirstActAFound = firstAct
                    newQ.append((droneResult, packageResult,newClientsLocation, newValue, firstAct))
            q=newQ
            time+=1
        if len(self.dronesName)==1:
            return (bestFirstActAFound,)
        return bestFirstActAFound

    def findProbabilty(self,clientsState,newClientsLocation):
        if ((clientsState.values(),newClientsLocation.values())) in self.clientsMovementsProbabilitiesCalculated.keys():
            return self.actionsCalculted[((clientsState.values(),newClientsLocation.values()))]
        prob=1
        movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        for client,value in clientsState.items():
            currentLocation= value['location']
            previosLocation= newClientsLocation[client]['location']
            for i in range (len(movements)):
                move= movements[i]
                if tuple(map(operator.add, previosLocation, move)) ==currentLocation:
                    prob*= value['probabilities'][i]
        self.actionsCalculted[((clientsState.values(), newClientsLocation.values()))]=prob
        return prob
    def getBestActionsByHeurisitic(self,dronesState,packagesState, clients,actions):
        minHfound= float('inf')
        actionResults= dict()
        for action in actions:
            hValue=0
            drones,packages= self.getResultForAction(dronesState, packagesState, action)
            for package,location in packages.items():
                if location in self.dronesName:
                    hValue+= self.getShortestPathToClient(package, clients,location, drones)
                else:
                    hValue += self.getShortestPathToPackage(location, drones)
            actionResults[action]= hValue
            if hValue< minHfound:
                minHfound=hValue
        result=actionResults.copy()
        for action,value in actionResults.items():
            if value > minHfound:
                result.pop(action)
        if len(result.keys())==1:
            return tuple(result.keys())[0]
        return tuple(result.keys())



    def getShortestPathToPackage(self,package, drones):
        minDistanceFound= float('inf')
        x_package= package[0]
        y_package = package[1]
        for drone,location in drones.items():
            x_drone = location[0]
            y_drone = location[1]
            dist= max(abs(x_package-x_drone), abs(y_package-y_drone))
            if dist<minDistanceFound:
                minDistanceFound=dist
        return minDistanceFound

    def getShortestPathToClient(self, packageToDeliver, clients,deliverDroneName,drones):
        x_drone = drones[deliverDroneName][0]
        y_drone = drones[deliverDroneName][1]
        for client,value in clients.items():
            if packageToDeliver in value['packages']:
                return self.getDistanceBetweenDroneAndPackage(drones[deliverDroneName],value['location'],value['probabilities'])
        return 0

    def getDistanceBetweenDroneAndPackage(self, droneLocation, clientLocation, clientProbabilities):
        if ((droneLocation, clientLocation, clientProbabilities)) in self.distanceBetweenDroneAndPackage.keys():
            return self.distanceBetweenDroneAndPackage[(droneLocation, clientLocation, clientProbabilities)]
        movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        t=0
        while clientLocation != droneLocation:
            for _ in range(1000):
                movement = random.choices(movements, weights=clientProbabilities)[0]
                new_coordinates = (clientLocation[0] + movement[0], clientLocation[1] + movement[1])
                if new_coordinates[0] < 0 or new_coordinates[1] < 0 or new_coordinates[0] >= len(self.map) or new_coordinates[1] >= len(self.map[0]):
                    continue
                break
            else:
                new_coordinates = (clientLocation[0], clientLocation[1])
            clientLocation = new_coordinates
            t+=1
        self.distanceBetweenDroneAndPackage[(droneLocation, clientLocation, clientProbabilities)]= t
        return t

    def getAllActions(self,drones,packages,clients ):
        if ((drones.values(),packages.values(),clients.values())) in self.actionsCalculted.keys():
            return self.actionsCalculted[((drones.values(),packages.values(),clients.values()))]
        currentClientLocations=set([value['location'] for client,value in clients.items()])
        dronesWithPackages= set([location for package,location in packages.items() if location in self.dronesName])
        actions = dict()
        for droneName,location in drones.items():
            currDroneActions = []
            currDroneActions.append(('wait', droneName))
            if droneName in dronesWithPackages:
                if location in currentClientLocations:
                    packagesWithDrone = set([package for package, location in packages.items() if location == droneName])
                    for client,value in clients.items():
                        if value['location']==location:
                            packagesDroneCanDeliverToClient = set(value['packages']).intersection(packagesWithDrone)
                            if len(packagesDroneCanDeliverToClient):
                                for package in packagesDroneCanDeliverToClient:
                                    currDroneActions.append(("deliver", droneName, str(client), str(package)))
            if location in packages.values():
                for packageName, packageLocation in packages.items():
                    if (location == packageLocation) and (packageName in self.packagesClientsWant) :
                            currDroneActions.append(("pick up", droneName, str(packageName)))
            x_location= int(location[0])
            y_location= int(location[1])
            if x_location>=1 and self.map[x_location-1][y_location] != 'I':
                currDroneActions.append(("move", droneName, (x_location-1, y_location)))
            if y_location>=1 and self.map[x_location][y_location-1] != 'I':
                currDroneActions.append(("move", droneName, (x_location, y_location-1)))
            if x_location<= len(self.map)-2 and self.map[x_location+1][y_location] != 'I':
                currDroneActions.append(("move", droneName, (x_location+1, y_location)))
            if y_location<=len(self.map[0])-2 and self.map[x_location][y_location+1] != 'I':
                currDroneActions.append(("move", droneName, (x_location, y_location+1)))
            actions[droneName] = currDroneActions
        if len(drones) == 1:
            res= [act for act in actions.values()][0]
            self.actionsCalculted[((drones.values(), packages.values(), clients.values()))] = res
            return res
        dataMatrix =[actions[i] for i in actions.keys()]
        res= list(itertools.product(*dataMatrix))
        index=set()
        for j in range (len(res)):
            action=res[j]
            pickUpPackages=set()
            for i in range (len(action)):
                droneAction= action[i]
                if droneAction[0] =='pick up':
                    if droneAction[2] in pickUpPackages:
                        index.add(j)
                        break
                    pickUpPackages.add(droneAction[2])
        finalRes= [res[i] for i in range (len(res)) if i not in index]
        self.actionsCalculted[((drones.values(), packages.values(), clients.values()))]= finalRes
        return finalRes


    def getResultForAction(self,drones,packages,action):
        """Returns all the actions that can be executed in the given
        state. The result should be a tuple (or other iterable) of actions
        as defined in the problem description file"""
        # if action == "reset":
        #     # self.reset_environment()
        #     return
        # if action == "terminate":
        #     # self.terminate_execution()
        if action[1] in self.dronesName:
            action_name = action[0]
            drone_name = action[1]

            if action_name == "wait":
                return drones, packages
            if action_name == "pick up":
                package = action[2]
                packages[package] = drone_name

            if action_name == "move":
                destination = action[2]
                drones[drone_name] = destination

            if action_name == "deliver":
                package = action[3]
                if len(packages) and package in packages.keys():
                    packages.pop(package)
            return drones, packages

        for atomic_action in action:
            action_name = atomic_action[0]
            drone_name = atomic_action[1]

            if action_name == "wait":
                return drones, packages
            if action_name == "pick up":
                package = atomic_action[2]
                packages[package] = drone_name

            if action_name == "move":
                destination = atomic_action[2]
                drones[drone_name] = destination

            if action_name == "deliver":
                package = atomic_action[3]
                if len(packages) and package in packages.keys():
                    packages.pop(package)
        return drones,packages



    def getNewClientsLocation(self,clients):
        movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        for client, properties in clients.items():
            for _ in range(1000):
                movement = random.choices(movements, weights=properties["probabilities"])[0]
                new_coordinates = (properties["location"][0] + movement[0], properties["location"][1] + movement[1])
                if new_coordinates[0] < 0 or new_coordinates[1] < 0 or new_coordinates[0] >= len(self.map) or \
                        new_coordinates[1] >= len(self.map[0]):
                    continue
                break
            else:
                new_coordinates = (properties["location"][0], properties["location"][1])
            assert new_coordinates
            properties["location"] = new_coordinates
        return clients

    def getImmediateReward(self, packages, drones, clients):
        reward=0
        packagesLocation= set(packages.values())
        packeagesToDeliver= packagesLocation.intersection(self.dronesName)
        if len(packeagesToDeliver):
            for client,value in clients.items():
                packagesClientWant= set(value['packages'])
                dronesInCurrentLocation =set([droneName for droneName,location in drones.items() if location==value['location']])
                packagesToDeliverToClient= [package for package,location in packages.items() if package in packagesClientWant and location in dronesInCurrentLocation]
                result= len(packagesToDeliverToClient)
                if result:
                    reward+= 10*result
        return reward
