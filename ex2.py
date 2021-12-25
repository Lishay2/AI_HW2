import itertools
import random
import operator
import copy
ids = ["316217835", "206824690"]


class EndOfGame(Exception):
    pass


class DroneAgent:
    def __init__(self, initial):
        self.map= initial['map']
        self.drones= initial['drones']
        self.dronesName= set(self.drones.keys())
        self.packages= initial['packages']
        self.clients= initial['clients']
        self.turnsToGo = initial['turns to go']
        self.factor=1
        self.actionsCalculated=dict()
        self.distanceBetweenDroneAndPackage=dict()
        self.clientsMovementsProbabilitiesCalculated= dict()
        self.packagesClientsWant = set()

        self.initialNumberOfTurns = initial['turns to go']
        self.timeToGain20Points=0
        self.timeToGain10Points=0
        self.flag20PointsCalculated= False
        self.initialNumberOfPackages= len(self.packages)

        for client, value in self.clients.items():
            for packagesClientWant in (set(value['packages'])):
                self.packagesClientsWant.add(packagesClientWant)

    def act(self, state):
        state= copy.deepcopy(state)
        if self.timeToGain20Points==0 and len(state['packages']) +2 == self.initialNumberOfPackages :
                self.timeToGain20Points = self.initialNumberOfTurns - state['turns to go']
        if len(state['packages'])==0:
            if self.timeToGain20Points!=0:
                if self.timeToGain20Points < state['turns to go']:
                    return "reset"
                return "terminate"
            return "reset"
        q=dict()
        maxValueFound= 0
        bestFirstActAFound=''
        firstActions = self.getAllActions(state['drones'],state['packages'],state['clients'])
        for action in firstActions:
            if action[0]=="deliver" or action[0]=="pick up":
                if len(self.dronesName) == 1:
                    return (action,)
                return action
            droneResult, packageResult = self.getResultForAction(state['drones'],state['packages'], action)
            newClientsLocation = self.getNewClientsLocation(state['clients'])
            newValue = self.getImmediateReward(packageResult, droneResult, state['clients'])
            if newValue >= maxValueFound:
                maxValueFound = newValue
                bestFirstActAFound = action
            q[action] = ((copy.deepcopy(droneResult),copy.deepcopy(packageResult), copy.deepcopy(newClientsLocation),newValue))
            # q.append((droneResult,packageResult,newClientsLocation, newValue, action))
        time=1
        while time< state['turns to go']:
            newQ=dict()
            for firstAct, values in q.items():
                droneState= values[0]
                packageState= values[1]
                clientsState = values[2]
                currentValue= values[3]
                newClientsLocation= self.getNewClientsLocation(clientsState)
                immediateReward = self.getImmediateReward(packageState, droneState, newClientsLocation)
                if immediateReward:
                    prob= self.findProbability(clientsState, newClientsLocation)
                else:
                    prob=0
                actions= self.getAllActions(droneState,packageState,newClientsLocation)
                bestActions, flagStopRunning= self.getBestActionsByHeuristic(droneState, packageState, newClientsLocation, actions)
                if bestActions in q.keys():
                    continue
                if flagStopRunning:
                    if len(self.dronesName) == 1:
                        return (firstAct,)
                    return firstAct
                droneResult, packageResult= self.getResultForAction(droneState,packageState,bestActions)
                newValue= currentValue+ self.factor*(immediateReward*prob)
                if newValue >= maxValueFound:
                    maxValueFound = newValue
                    bestFirstActAFound = firstAct
                    newQ[firstAct]=((copy.deepcopy(droneResult),copy.deepcopy(packageResult), copy.deepcopy(newClientsLocation),newValue))
            q=newQ
            time+=1
        if len(self.dronesName)==1:
            return (bestFirstActAFound,)
        return bestFirstActAFound

    def findProbability(self, clientsState, newClientsLocation):
        if ((clientsState.values(),newClientsLocation.values())) in self.clientsMovementsProbabilitiesCalculated.keys():
            return self.actionsCalculated[((clientsState.values(), newClientsLocation.values()))]
        prob=1
        movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        for client,value in clientsState.items():
            currentLocation= value['location']
            previosLocation= newClientsLocation[client]['location']
            for i in range (len(movements)):
                move= movements[i]
                if tuple(map(operator.add, previosLocation, move)) ==currentLocation:
                    prob*= value['probabilities'][i]
        self.actionsCalculated[((clientsState.values(), newClientsLocation.values()))]=prob
        return prob

    def getBestActionsByHeuristic(self, dronesState, packagesState, clients, actions):
        dronesInitialDistance=dict()
        initialH=0
        for package, location in packagesState.items():
            if location in self.dronesName:
                distanceToClient=self.getShortestPathToClient(package, clients, location, dronesState)
                dronesInitialDistance[location]= distanceToClient
                initialH+=distanceToClient
            else:
                distanceToPackage= self.getShortestPathToPackage(location, dronesState)
                dronesInitialDistance[location] =distanceToPackage
                initialH += distanceToPackage
        minHfound= float('inf')
        actionResults= dict()
        for action in actions:
            if action[0]=="deliver" or action[0]=="pick up":
                return tuple(), True
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
            if value > initialH or value > minHfound:
                result.pop(action)
        if len(result.keys())==1:
            return tuple(result.keys())[0], False
        return tuple(result.keys()), False

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
        drones= copy.deepcopy(drones)
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
            minDist= max(abs(clientLocation[0]-droneLocation[0]), abs(clientLocation[1]-droneLocation[1]))
            bestNextDroneLocation=droneLocation
            for movement in movements:
                newDroneCoordinated= (clientLocation[0] + movement[0], clientLocation[1] + movement[1])
                newDist= max(abs(clientLocation[0]-newDroneCoordinated[0]), abs(clientLocation[1]-newDroneCoordinated[1]))
                if newDist< minDist:
                    minDist= newDist
                    bestNextDroneLocation= newDroneCoordinated
            t+=1
            droneLocation=bestNextDroneLocation
        self.distanceBetweenDroneAndPackage[(droneLocation, clientLocation, clientProbabilities)]= t
        return t

    def getAllActions(self,drones,packages,clients ):
        drones= copy.deepcopy(drones)
        packages = copy.deepcopy(packages)
        clients = copy.deepcopy(clients)
        if ((drones.values(),packages.values(),clients.values())) in self.actionsCalculated.keys():
            return self.actionsCalculated[((drones.values(), packages.values(), clients.values()))]
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
                numberOfPackagesWithDrone= len([packageName for packageName, packageLocation in packages.items() if packageLocation==droneName])
                if numberOfPackagesWithDrone <2:
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

            if x_location>=1 and y_location>=1 and self.map[x_location-1][y_location-1] != 'I':
                currDroneActions.append(("move", droneName, (x_location-1, y_location-1)))

            if  y_location>=1 and x_location<= len(self.map)-2 and self.map[x_location+1][y_location-1] != 'I':
                currDroneActions.append(("move", droneName, (x_location+1, y_location-1)))

            if y_location<=len(self.map[0])-2 and x_location>=1 and self.map[x_location-1][y_location+1] != 'I':
                currDroneActions.append(("move", droneName, (x_location-1, y_location+1)))

            if y_location<=len(self.map[0])-2 and x_location<= len(self.map)-2 and self.map[x_location+1][y_location+1] != 'I':
                currDroneActions.append(("move", droneName, (x_location+1, y_location+1)))

            actions[droneName] = currDroneActions
        if len(drones) == 1:
            res= [act for act in actions.values()][0]
            self.actionsCalculated[((drones.values(), packages.values(), clients.values()))] = res
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
        self.actionsCalculated[((drones.values(), packages.values(), clients.values()))]= finalRes
        return finalRes

    def getResultForAction(self,drones,packages,action):
        """Returns all the actions that can be executed in the given
        state. The result should be a tuple (or other iterable) of actions
        as defined in the problem description file"""
        # if action == "reset":
        #     self.reset_environment()
        #     return
        # if action == "terminate":
        #     self.terminate_execution()
        drones= copy.deepcopy(drones)
        packages = copy.deepcopy(packages)
        action = copy.deepcopy(action)
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

    # def reset_environment(self, initial):
    #     self.map = initial['map']
    #     self.drones = copy.deepcopy(initial['drones'])
    #     self.dronesName = set(self.drones.keys())
    #     self.packages = copy.deepcopy(initial['packages'])
    #     self.clients = copy.deepcopy(initial['clients'])
    #     self.turnsToGo -= 1
    #     self.factor = 1
    #     self.actionsCalculated = dict()
    #     self.distanceBetweenDroneAndPackage = dict()
    #     self.clientsMovementsProbabilitiesCalculated = dict()
    #     self.packagesClientsWant = set()
    #     self.initialNumberOfPackages = len(self.packages)
    #
    # def terminate_execution(self):
    #     print(f"End of game, your score is {self.score}!")
    #     print(f"-----------------------------------")
    #     raise EndOfGame
