import sys, platform, os, time
from pathlib import Path
import numpy as np

from diambraArena.utils.splashScreen import DIAMBRASplashScreen
import grpc
import diambra_pb2
import diambra_pb2_grpc

def diambraApp(diambraAppPath, pipesPath, envId, romsPath, render):
    print("Args = ", diambraAppPath, pipesPath, envId, romsPath, render)

    if diambraAppPath != "":
        command = '{} --pipesPath {} --envId {}'.format(diambraAppPath, pipesPath, envId)
    else:
        dockerRomsFolder = "/opt/diambraArena/roms"
        dockerPipesFolder = "/tmp/"
        dockerImageName = "diambra/diambra-app:main"
        dockerContainerName = "container"+envId
        romsVol = '--mount src={},target="{}",type=bind '.format(romsPath, dockerRomsFolder)
        homeFolder = os.getenv("HOME")
        if render:
            x11exec = os.path.join(pipesPath, "x11docker")
            command  = '{} --cap-default --hostipc --network=host --name={}'.format(x11exec, dockerContainerName)
            command += ' --wm=host --pulseaudio --size=1024x600 -- --privileged'
            command += ' {} --mount src="{}",target="{}",type=bind'.format(romsVol, pipesPath, dockerPipesFolder)
            command += ' -e HOME=/tmp/ --mount src="{}/.diambraCred",target="/tmp/.diambraCred",type=bind'.format(homeFolder)
            command += ' -- {} &>/dev/null & sleep 4s;'.format(dockerImageName)
            command += ' docker exec -u $(id -u) --privileged -it {}'.format(dockerContainerName)
            command += ' sh -c "set -m; cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}";'.format(dockerPipesFolder, envId)
            command += ' pkill -f "bash {}*"'.format(x11exec)
        else:
            command  = 'docker run --user $(id -u) -it --rm --privileged {}'.format(romsVol)
            command += ' --mount src="{}",target="{}",type=bind'.format(pipesPath, dockerPipesFolder)
            command += ' -e HOME=/tmp/ --mount src="{}/.diambraCred",target="/tmp/.diambraCred",type=bind'.format(homeFolder)
            command += ' --name {} {}'.format(dockerContainerName, dockerImageName)
            command += ' sh -c "cd /opt/diambraArena/ &&'
            command += ' ./diambraApp --pipesPath {} --envId {}"'.format(dockerPipesFolder, envId)

    print("Command = ", command)
    os.system(command)

# DIAMBRA Env Gym
class diambraArenaLib:
    """Diambra Environment gym interface"""

    def __init__(self):

        self.pipesPath = os.path.dirname(os.path.abspath(__file__))

        # Opening gRPC channel
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = diambra_pb2_grpc.EnvServerStub(self.channel)

        # Splash Screen
        DIAMBRASplashScreen()

    # Transforming env kwargs to string
    def envSettingsToString(self):

        maxCharToSelect = 3
        sep = ","
        endChar = "+"

        output = ""

        output += "envId"+            sep+"2"+sep + self.envSettings["envId"] + sep
        output += "gameId"+           sep+"2"+sep + self.envSettings["gameId"] + sep
        output += "continueGame"+     sep+"3"+sep + str(self.envSettings["continueGame"]) + sep
        output += "showFinal"+        sep+"0"+sep + str(int(self.envSettings["showFinal"])) + sep
        output += "stepRatio"+        sep+"1"+sep + str(self.envSettings["stepRatio"]) + sep
        output += "player"+           sep+"2"+sep + self.envSettings["player"] + sep
        output += "difficulty"+       sep+"1"+sep + str(self.envSettings["difficulty"]) + sep
        output += "character1"+       sep+"2"+sep + self.envSettings["characters"][0][0] + sep
        output += "character2"+       sep+"2"+sep + self.envSettings["characters"][1][0] + sep
        for iChar in range(1, maxCharToSelect):
            output += "character1_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][0][iChar] + sep
            output += "character2_{}".format(iChar+1)+     sep+"2"+sep + self.envSettings["characters"][1][iChar] + sep
        output += "charOutfits1"+     sep+"1"+sep + str(self.envSettings["charOutfits"][0]) + sep
        output += "charOutfits2"+     sep+"1"+sep + str(self.envSettings["charOutfits"][1]) + sep

        # SFIII Specific
        output += "superArt1"+        sep+"1"+sep + str(self.envSettings["superArt"][0]) + sep
        output += "superArt2"+        sep+"1"+sep + str(self.envSettings["superArt"][1]) + sep
        # UMK3 Specific
        output += "tower"+            sep+"1"+sep + str(self.envSettings["tower"]) + sep
        # KOF Specific
        output += "fightingStyle1"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][0]) + sep
        output += "fightingStyle2"+   sep+"1"+sep + str(self.envSettings["fightingStyle"][1]) + sep
        for idx in range(2):
            output += "ultimateStyleDash"+str(idx+1)+  sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][0]) + sep
            output += "ultimateStyleEvade"+str(idx+1)+ sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][1]) + sep
            output += "ultimateStyleBar"+str(idx+1)+   sep+"1"+sep + str(self.envSettings["ultimateStyle"][idx][2]) + sep

        output += "disableKeyboard"+  sep+"0"+sep + str(int(self.envSettings["disableKeyboard"])) + sep
        output += "disableJoystick"+  sep+"0"+sep + str(int(self.envSettings["disableJoystick"])) + sep
        output += "rank"+             sep+"1"+sep + str(self.envSettings["rank"]) + sep
        output += "recordConfigFile"+ sep+"2"+sep + self.envSettings["recordConfigFile"] + sep

        output += endChar

        return output

    # Send environment settings, retrieve environment info and int variables list
    def initEnv(self, envSettings)
        envSettingsString = self.envSettingsToString()
        response = self.stub.SendEnvSettings(diambra_pb2.EnvSettings(settings=envSettingsString))
        self.intDataVarsList = response.intDataList.split(",")
        self.intDataVarsList.remove("")
        return response.envInfo

    # Set frame size
    def setFrameSize(self, hwcDim):
        self.height = hwcDim[0]
        self.width  = hwcDim[1]
        self.nChan  = hwcDim[2]
        self.frameDim = hwcDim[0] * hwcDim[1] * hwcDim[2]

    # Read data
    def readData(self, obs):
        obs = obs.split(",")

        data = {}

        idx = 0
        for var in self.intDataVarsList:
            data[var] = int(obs[idx])
            idx += 1

        for var in self.boolDataVarsList:
            data[var] = bool(int(obs[idx]))
            idx += 1

        return data, obs[-2]

    # Read frame
    def readFrame(self, frame):
        frame = np.frombuffer(frame, dtype='uint8').reshape(self.height, self.width, self.nChan)

        cv2.namedWindow("test",cv2.WINDOW_GUI_NORMAL)
        cv2.imshow("test", frame)
        cv2.waitKey(0)

        return frame

    # Reset the environment
    def reset(self):
        response = self.stub.CallReset(diambra_pb2.Empty())
        data, playerSide = self.readData(response.observation)
        frame = self.readFrame(response.frame)

        return frame, data, playerSide

    # Step the environment (1P)
    def step1P(self, movP1, attP1):
        response = self.stub.CallStep1P(diambra_pb2.Command(P1mov=movP1, P1att=attP1))
        data, _ = self.readData(response.observation)
        frame = self.readFrame(response.frame)
        return frame, data

    # Step the environment (2P)
    def step2P(self, movP1, attP1, movP2, attP2):
        response = self.stub.CallStep1P(diambra_pb2.Command(P1mov=movP1, P1att=attP1,
                                                       P2mov=movP2, P2att=attP2))
        data, _ = self.readData(response.observation)
        frame = self.readFrame(response.frame)
        return frame, data

    # Closing DIAMBRA Arena
    def close(self):
         self.stub.CallClose(diambra_pb2.Empty())
         self.channel.close() # self.stub.close()
