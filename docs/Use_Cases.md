# Chapter 1
## Introduction to the Tutorial

This tutorial is intended to introduce the user to the TDcoSim tool. The user will be guided
through the creation and development of multiple test cases so as to gain familiarity with the 
basic features and functionalities of the tool. The tutorial project is developed in a 
sequential manner in which each of the use case builds upon what has been completed in the 
previous test case. 

***
Note: In order to execute the Tutorial, user needs to have PSSE version 30.0.0 or latest and 
OpenDSS v1.0 or latest.
***

# Chapter 2

## Understanding the Config File

Before starting the operation of TDcoSim tool and running test cases, it is mandatory to understand the configuration file which sets up the simulation conditions. This chapter describes the different components of the configuration file and guides the user methods to set up the simulation.

1. "cosimHome":"C:\\Rojan\\NERC_TnD_Project\\pvder_refac\\NERC_PSSE_OpenDSS\\CoSimulator"

Variable "cosimHome" defines the parent path of the TDcoSim tool. The user needs to specify the parent path of the tool once the tool is installed in their workstation.

2. "psseConfig":{
        "rawFilePath":"C:\\Rojan\\NERC_TnD_Project\\pvder_refac\\NERC_PSSE_OpenDSS\\SampleData\\TNetworks\\118bus\\case118.raw",
        "dyrFilePath":"C:\\Rojan\\NERC_TnD_Project\\pvder_refac\\NERC_PSSE_OpenDSS\\SampleData\\TNetworks\\118bus\\case118.dyr"        
    }
    
 Variable "psseConfig" defines the path for the PSS/E transmission system loadflow and dynamic case file that will be used in the TDcoSim tool. "rawFilePath" specifies the path for the loadflow case file for the transmission system. "dyrFilePath" specifies the path for the dynamic case file for the transmission system.
 
 3. "openDSSConfig":{        
        "defaultFeederConfig":{
            "filePath":["C:\\Rojan\\NERC_TnD_Project\\pvder_refac\\NERC_PSSE_OpenDSS\\SampleData\\DNetworks\\123Bus\\case123ZIP.dss"],
            "solarFlag":0,
            "solarPenetration":0.0
            }
            }
            
 Variable "openDSSConfig" defines the path for the distribution system network used in the TDcoSim tool and configuration for the DER in the distribution system. There are two configuration used for the distribution system and DER, namely : "defaultFeederConfig" and "manualFeederConfig". For each configuration there are other variables that specify the path of the distribution network, penetration level of DER and status of the DER. 
 
 Variable "filePath" specifies the path for the OpenDSS File used in the tool.
 
 Variable "solarFlag" specifies whether the DER are present in the distribution system or not.
 
 Variable "solarPenetration" specifies the penetration level of DER within the distribution network.
 
 4. "manualFeederConfig":{
            "nodes": [
                {
                    "nodenumber": 2,
                    "filePath": ["C:\\Rojan\\NERC_TnD_Project\\pvder_refac\\NERC_PSSE_OpenDSS\\SampleData\\DNetworks\\123Bus\\case123ZIP.dss"],
                    "solarFlag":0,
                    "solarPenetration":0.0,
                    "DERParameters":{
                        "power_rating": 50,
                        "voltage_rating":174,
                        "SteadyState": true,
                        "V_LV1": 0.70,
                        "V_LV2": 0.88,
                        "t_LV1_limit": 10.0,  
                        "t_LV2_limit": 20.0,
                        "LVRT_INSTANTANEOUS_TRIP": false,
                        "LVRT_MOMENTARY_CESSATION": false,
                        "pvderScale": 1.0,
                        "solarPenetrationUnit":"kw",
                        "avoidNodes":["sourcebus","rg60"],
                        "dt":0.008333
                    }
                }
                
  Variable "manualFeederConfig" manually specifies the configuration of the test distribution network. Using manual configuration, the transmission bus where the distribution system is to be connected is specified. Manual configuration has variable "nodes" which specifies the configuration each of the distribution system.
  
  Variable "nodenumber" specifies the transmission bus where the distribution system is to be connected.
  
  Variable "filePath" specifies the path for the OpenDSS File used in the tool.
  
  Variable "solarFlag" specifies whether the DER are present in the distribution system or not.
 
 Variable "solarPenetration" specifies the penetration level of DER within the distribution network.
 
 Variable "DERParameters" specifies the configuration of DERs to be used in the distribution system. Variable "DERParameters" have more variable associated with it which specifies the different parameters of the DER.
 
Variable "power_rating" specifies the power rating of DER in kW.

Variable "voltage_rating":174 specifies the voltage rating of an individual DER to be connected in the distribution system. The tool automatically adds a transformer to connect the DER with the distribution system and match the voltage at both ends of the transformer.

Variable "SteadyState" specifies whether the DER is to be initialized in steady state or not before connecting ot to the distribution system.
                        
Variable "V_LV1" specifies the under-voltage 1 trip set point. This is the lower limit of the DER trip voltage.

Variable "V_LV2" specifies the under-voltage 2 trip set point. This is the upper limit of the DER trip voltage.

Variable "t_LV1_limit" specifies the under-voltage 1 trip time set point. This is the trip time associated with lower limit of the DER trip voltage. Note that the timer have a scaling factor of 10 associated with them. 10 secs specification in the variable transforms to actual trip time of 1 secs.

Variable "t_LV2_limit" specifies the under-voltage 2 trip time set point. This is the trip time associated with upper limit of the DER trip voltage. Note that the timer have a scaling factor of 10 associated with them. 10 secs specification in the variable transforms to actual trip time of 1 secs.

Variable "pvderScale": specifies the scaling factor associated with the individual DER power output. This helps to increase the rating of DER at a particular location thereby reducing the number of DER components in a distribution feeder which helps to speed up the overall simulation.

Varibale "solarPenetrationUnit" specifies the unit of solar penetration in the distribution system.

Variable "avoidNodes": specifies the nodes in the distribution system that are to be avoided when placing the DER. As of now the tool automatically places the DER at different nodes of the distribution system and avoids the nodes mentioned under the variable "avoidNodes".

Variable "dt" specifies the solution time step for the DER object.   

5. After specifying the transmission system, distribution system and DER, the next set of variables in the configuration file specifies the simulation configuration. Variable "simulationConfig" specifies the simulation configuration. TDcoSim tool has two sets of simulation configuration 1. Dynamic and 2. Static.

Variable "dynamicConfig" specifies the various events in the dynamic simulation. The dynamic events are sequentially listed in the variable "dynamicConfig".

Variable "staticConfig" specifies the configuration for the static simulation.

Variable "protocol" specifies the nature of coupling between Transmission system and Distribution System.

6. Variable "outputConfig" specifies the output filename and type of the simulation results file. Please note that the TDcoSim tool do not have result analysis tool embedded in it in its current version. It is advised that the user uses data analysis tool and scripts to analyze the output of the simulation.


# Chapter 3

## Starting TDcoSim

This chapter walks the user through the step to start the simulation after setting up the configuration file. To start the simulation the user needs to open the folder where the TDcoSim tool is installed. Once the folder where the tool is installed is identified the user needs to open the "CoSimulator" branch and open up a command window from the "CoSimulator" folder. To do that the user needs to go the box on the folder where we specify path and type Shift+C+M+D as shown in Figure below.

![Open_CMD](images/Open_CMD.png)

Figure: Opening Command Window from Cosimulator Folder.

Once the command window is opened. The user can type in the following command, as shown in Figure below, followed by Enter to start the simulation using TDcoSim tool.

                        "python main2.py > log_file.txt"
                        
![Starting_TDcoSim_tool](images/Starting_TDcoSim_tool.PNG)

Figure: Starting TDcoSim tool from Command Window.

python starts the python process and runs the python code "main2.py" which starts the TDcoSim tool. '>' specifies the output logfile. In the example above the output log file name is 'log_file.txt'.







        
