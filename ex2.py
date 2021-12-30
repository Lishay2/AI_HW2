import itertools
import random
import operator
import copy
import math
ids = ["316217835", "206824690"]


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
        self.calculatedActs= dict()
        self.packagesClientsWant = set()


        self.initialNumberOfTurnes = initial['turns to go']
        self.lastResetTurn=self.initialNumberOfTurnes
        self.timeToGain20Points=0
        self.timeToGain10Points=0
        self.flag20PointsCalculated= False
        self.initialNumberOfPackages= len(self.packages)
        for client, value in self.clients.items():
            for packagesClientWant in (set(value['packages'])):
                self.packagesClientsWant.add(packagesClientWant)

    def act(self, state):
        state= copy.deepcopy(state)
        if self.initialNumberOfPackages==1 and len(state['packages'])==0:
            if self.timeToGain20Points==0:
                self.timeToGain20Points = 2*(self.initialNumberOfTurnes- state['turns to go'])
            else:
                timeSinceReset= self.lastResetTurn -state['turns to go']
                self.timeToGain20Points= int(math.ceil((self.timeToGain20Points+ (2*timeSinceReset) )/2))
        if self.initialNumberOfPackages>=2 and  len(state['packages']) +2 == self.initialNumberOfPackages :
            if self.timeToGain20Points==0:
                self.timeToGain20Points = self.initialNumberOfTurnes- state['turns to go']
            else:
                timeSinceReset= self.lastResetTurn -state['turns to go']
                self.timeToGain20Points= int(math.ceil((self.timeToGain20Points+ timeSinceReset )/2))
        if self.initialNumberOfPackages==0:
            return "terminate"
        if len(state['packages'])==0:
            self.lastResetTurn= state['turns to go']
            if self.timeToGain20Points==0:
                return "reset"
            if self.timeToGain20Points <= state['turns to go']:
                return "reset"
            return "terminate"
        if (state['drones'].values(), state['drones'].values(), state['clients'].values()) in self.calculatedActs:
            return self.calculatedActs[(state['drones'].values(), state['drones'].values(), state['clients'].values())]
        firstActions = self.getAllActions(state['drones'],state['packages'],state['clients'])
        bestActions = self.getBestActionsByHeurisitic(state['drones'], state['packages'],state['clients'], firstActions)
        return bestActions

    def getBestActionsByHeurisitic(self,dronesState,packagesState, clients,actions):
        packagesPickedUp=set()
        dronesBestAction= dict()
        for droneName,location in dronesState.items():
            dronesBestAction[droneName]= self.findBestActionForSingleDrone(droneName,location,clients,actions,dronesState, packagesState,packagesPickedUp)
            if dronesBestAction[droneName][0]=="pick up":
                packagesPickedUp.add(dronesBestAction[droneName][2])
        if len(self.dronesName)==1:
            result=tuple(dronesBestAction.values())[0]
            return (tuple(result),)
        result=[]
        for droneName,bestAction in dronesBestAction.items():
            result.append(tuple(bestAction))
        return tuple(result)


    def findBestActionForSingleDrone(self, droneName,dronesLocation,clients,actions,dronesState, packagesState,removedPickUpActionByPackage):
        dronesAction=set()
        packagesLocationWithDrone = [location for package, location in packagesState.items() if location == droneName]
        packagesWithDrone = [package for package, location in packagesState.items() if location == droneName]
        packagesForPickUp = [package for package, location in packagesState.items() if location not in self.dronesName]
        clientsWhoWantDelivery= [client for client,value in clients.items() if set(value['packages']).intersection(set(packagesState.keys()))]
        otherDronesForPickUp= [drone for drone,location in dronesState.items() if drone!=droneName and len([packageLocation for packageLocation in packagesLocationWithDrone if packageLocation==drone])<2]
        if len(self.dronesName)>1:
            for action in actions:
                for atomicAction in action:
                    if atomicAction[1]== droneName:
                        if atomicAction[0] == "pick up" and atomicAction[2] in removedPickUpActionByPackage:
                            break
                        if not (atomicAction[0] == "pick up" and len(packagesWithDrone) > 0 and len(packagesForPickUp) == 1 and len(otherDronesForPickUp) and len(clientsWhoWantDelivery)>1):
                            dronesAction.add(atomicAction)
                        break
            actions= tuple(dronesAction)
        actionResults= dict()
        bestActionsFound= []
        for action in actions:
            actionResults[action] = 0
            if action[0] == "deliver":
                bestActionsFound.append(action)
            if action[0] == "pick up":
                bestActionsFound.append(action)
        if len(bestActionsFound)>0:
            if len(bestActionsFound)==1 and tuple(bestActionsFound)[0]=="pick up":
                return tuple(bestActionsFound)[0]
            for action in bestActionsFound:
                if action[0]== "deliver":
                    return action
            return tuple(bestActionsFound)[0]
        minHfound= float('inf')
        actionResults=dict()
        actionDeliver= None
        actionPickup=None
        valueDeliver=0
        valuePickUp=0
        if len(packagesWithDrone)>=1:
            valueDeliver, actionDeliver= self.findBestActionForFutureDeliver(droneName,dronesLocation, packagesWithDrone, clients,actions)
        if len(packagesWithDrone)<2 and len(packagesForPickUp):
            valuePickUp, actionPickup = self.findBestActionForFuturePickup(droneName, dronesLocation, packagesState,actions)
        if actionDeliver == None and actionPickup==None:
            if len(actions)==0:
                a=3
            return actions[0]
        if actionDeliver== None:
            return actionPickup
        if actionPickup==None:
            return actionDeliver
        if valuePickUp>valueDeliver:
            return actionDeliver
        return actionPickup


    def findBestActionForFutureDeliver(self,droneName,dronesLocation, packagesWithDrone, clients,actions):
        movements = [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)]
        x_drone = dronesLocation[0]
        y_drone = dronesLocation[1]
        minDistFound = float('inf')
        if len(actions)==0:
            a=2
        bestActionFound = actions[0]
        clientsForDeliver= [ [client,value]  for client, value in clients.items() if len(set(value['packages']).intersection(set(packagesWithDrone)))]
        for client in clientsForDeliver:
            clientLocation= client[1]['location']
            dist = max(abs(clientLocation[0] - x_drone), abs(clientLocation[1] - y_drone))
            if dist==1:
                maxP=-1
                nextClientLocation=tuple()
                value= client[1]
                for i in range (len(value['probabilities'])):
                    new_coordinates = (clientLocation[0] + movements[i][0], clientLocation[1] + movements[i][1])
                    if new_coordinates[0] < 0 or new_coordinates[1] < 0 or new_coordinates[0] >= len(self.map) or \
                            new_coordinates[1] >= len(self.map[0]):
                        continue
                    if value['probabilities'][i]> maxP:
                        maxP=value['probabilities'][i]
                        nextClientLocation= new_coordinates
                if dronesLocation== nextClientLocation:
                    nextDroneAction= [action for action in actions if action[0]=="wait"]
                else:
                    nextDroneAction=[action for action in actions if len(action)>=3 and action[2]==nextClientLocation]
                    if len(nextDroneAction)==0:
                        nextDroneAction = [action for action in actions if action[0]!="wait" and max(abs(clientLocation[0] - action[2][0]), abs(clientLocation[1] - action[2][1]))]
                if len(nextDroneAction)>1:
                    nextDroneAction= nextDroneAction[0]
                if nextDroneAction:
                    result= tuple(nextDroneAction)
                    if len(result)==1:
                        result=result[0]
                    return 1, result
            else:
                for action in actions:
                    if action[0] == "wait":
                        continue
                    dist=max(abs(clientLocation[0] - action[2][0]), abs(clientLocation[1] - action[2][1]))
                    if dist< minDistFound:
                        minDistFound=dist
                        bestActionFound=action
        return minDistFound, bestActionFound

    def findBestActionForFuturePickup(self,droneName, dronesLocation, packages,actions):
        minDistFound = float('inf')
        bestActionFound = ''
        x_drone = dronesLocation[0]
        y_drone = dronesLocation[1]
        packagesForPickUp= [location  for package,location in packages.items() if not(location in self.dronesName)]
        for action in actions:
            for packageLocation in packagesForPickUp:
                if action[0]=="wait":
                    dist=1
                    dist+=max(abs(packageLocation[0] - x_drone), abs(packageLocation[1] -y_drone))
                else:
                    dist = max(abs(packageLocation[0] - action[2][0]), abs(packageLocation[1] -action[2][1]))
                if dist < minDistFound:
                    minDistFound = dist
                    bestActionFound = action
        if minDistFound == float('inf'):
            a=2
        return minDistFound, bestActionFound


    def getAllActions(self,drones,packages,clients ):
        drones= copy.deepcopy(drones)
        packages = copy.deepcopy(packages)
        clients = copy.deepcopy(clients)
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
        while len(action)==1:
            action=action[0]
        drones= copy.deepcopy(drones)
        packages = copy.deepcopy(packages)
        action = copy.deepcopy(action)
        if len(action) == 1:
            a = 2
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

