import cmath
import math
import pdb

import six
import numpy as np
from scipy.integrate import ode
from pvder.DER_wrapper import DERModel
from pvder.simulation_events import SimulationEvents
from pvder import utility_functions

from tdcosim.model.opendss.opendss_data import OpenDSSData
from tdcosim.model.opendss.model.pvderaggregation.procedure.pvder_procedure import PVDERProcedure


class PVDERAggregatedModel(object):
#===================================================================================================
	def __init__(self):
		OpenDSSData.data['DNet']['DER'] = {}
		OpenDSSData.data['DNet']['DER']['PVDERData'] = {}
		OpenDSSData.data['DNet']['DER']['PVDERData'].update({'lowSideV':{},'PNominal':{},
		'QNominal':{}})
		OpenDSSData.data['DNet']['DER']['PVDERMap'] = {}
		self._pvders = {}
		self._nEqs = {}

#===================================================================================================
	def getDERRatedPower(self,powerRating,voltageRating):
		"""Return actual real and reactive power rating of DER for given power and voltage rating.
		Args:
			 powerRating (float): Rated power of DER in kW. 
			 voltageRating (float): Rated voltage of DER in L-G RMS. 
		"""
		try:
			DERFilePath = OpenDSSData.config['myconfig']['DERFilePath']
			DERModelType = OpenDSSData.config['myconfig']['DERModelType']

			Va = cmath.rect(voltageRating*math.sqrt(2),0.0)
			Vb = utility_functions.Ub_calc(Va)
			Vc = utility_functions.Uc_calc(Va)
		
			PVDER_model = DERModel(modelType=DERModelType,events=events,configFile=DERFilePath,
									powerRating = powerRating*1e3,VrmsRating = voltageRating,
									gridVoltagePhaseA = Va,
									gridVoltagePhaseB = Vb,
									gridVoltagePhaseC = Vc,
									gridFrequency=2*math.pi*60.0,
									standAlone=False,steadyStateInitialization=True)
			self.PV_model = PVDER_model.DER_model

			return DER_model.S_PCC.real*DER_model.Sbase,DER_model.S_PCC.imag*DER_model.Sbase	
		except:
			OpenDSSData.log()

#===================================================================================================
	def setup(self, S0, V0):
		try:
			# set the random number seed
			randomSeed = 2500
			np.random.seed(randomSeed)

			DNet=OpenDSSData.data['DNet']
			myconfig=OpenDSSData.config['myconfig']
			if myconfig['DERSetting'] == 'PVPlacement':
				PVPlacement = True
				nSolar=len(myconfig['DERParameters']['PVPlacement']) #Number of solarpv DERs
			elif myconfig['DERSetting'] == 'default':
				PVPlacement = False
				feeder_load=0 # rating will be in kVA as Default
				for entry in S0['P']: #Sum all the loads in the feeder
					if myconfig['DERParameters']['default']['solarPenetrationUnit']=='kva':
						feeder_load+=abs(S0['P'][entry]+S0['Q'][entry]*1j)
					elif myconfig['DERParameters']['default']['solarPenetrationUnit']=='kw':
						feeder_load+=S0['P'][entry]
				# number of 50 kVA solar installtions required
				nSolar=int(np.ceil((feeder_load/myconfig['DERParameters']['default']['powerRating'])*\
				myconfig['DERParameters']['default']['solarPenetration']))
			else:
				raise ValueError('{} is not a valid DER setting in config file'.format(
				myconfig['DERSetting']))

			# find all three phase nodes
			threePhaseNode=[]
			for node in V0:
				count=0
				for phase in V0[node]:
					count+=1
				if count==3 and node not in myconfig['DERParameters']['avoidNodes']: # three phase node
					threePhaseNode.append(node)

			if PVPlacement:
				invalid_nodes = set(myconfig['DERParameters']['PVPlacement'].keys()).difference(
				threePhaseNode)
				if not invalid_nodes:
					threePhaseNode=list(myconfig['DERParameters']['PVPlacement']) #Get list of D nodes
				else:
					raise ValueError('Config file contains following invalid nodes:{}'.format(
					invalid_nodes))

			# create instances of pvder
			for n in range(nSolar):
				self._pvders[n]=PVDERProcedure()

			# now map each solar to the available nodes
			nThreePhaseNode=len(threePhaseNode); count=0
			for entry in self._pvders:
				if not PVPlacement:
					thisKey=threePhaseNode[np.random.randint(0,nThreePhaseNode)]
				else:
					thisKey=threePhaseNode[count]
					
				if thisKey not in DNet['DER']['PVDERMap']:
					DNet['DER']['PVDERMap'][thisKey]={}
					DNet['DER']['PVDERMap'][thisKey]['nSolar_at_this_node']=0
				DNet['DER']['PVDERMap'][thisKey][DNet['DER']['PVDERMap'][thisKey]\
				['nSolar_at_this_node']]=entry
				DNet['DER']['PVDERMap'][thisKey]['nSolar_at_this_node']+=1

				self._pvders[entry].setup(thisKey,V0[thisKey])#Pass both node id and V during DER setup
				self.initialize_PQVnominal(thisKey,self._pvders[entry]._pvderModel.PV_model)
				count+=1

			for entry in DNet['DER']['PVDERMap']:
				thisNode=DNet['DER']['PVDERData'][entry]={}
				thisNode['Vmag']={}

			self.pvIDIndex=self._pvders.keys() # index for variables based on ID
			if six.PY3:
				self.pvIDIndex=list(self.pvIDIndex)
			self.pvIDIndex.sort()# sort the index and use this as the order

			y0=[]; t0=0.0
			for n in range(len(self.pvIDIndex)):
				y0.extend(self._pvders[self.pvIDIndex[n]]._pvderModel.lastSol)
				self._nEqs[self.pvIDIndex[n]]=self._pvders[self.pvIDIndex[n]]._pvderModel.PV_model.n_ODE

			self.integrator=ode(self.funcval,self.jac).set_integrator('vode',method='bdf',
			rtol=1e-4,atol=1e-4)
			self.integrator.set_initial_value(y0,t0)

			return DNet['DER']['PVDERMap']
		except:
			OpenDSSData.log(msg="Failed Setup PVDERAGG")

#===================================================================================================
	def initialize_PQVnominal(self,node,DERModel):
		"""Initialize Pnominal and Qnominal."""
		try:
			myconfig=OpenDSSData.config['myconfig']
			initializeWithActual = myconfig['initializeWithActual']
		
			if initializeWithActual:
				DERRatingReal = DERModel.S_PCC.real*DERModel.Sbase
				DERRatingImag = DERModel.S_PCC.imag*DERModel.Sbase
		
			if myconfig['DERSetting'] == 'PVPlacement':
				 lowSideV = myconfig['DERParameters']['PVPlacement'][node]['VrmsRating'] 
				 
				 if initializeWithActual:
					 PNominal = (DERRatingReal/1e3)*\
					 myconfig['DERParameters']['PVPlacement'][node]['pvderScale']
					 QNominal = (DERRatingImag/1e3)*\
					 myconfig['DERParameters']['PVPlacement'][node]['pvderScale']
				 else:
					 PNominal = myconfig['DERParameters']['PVPlacement'][node]['powerRating']*\
					 myconfig['DERParameters']['PVPlacement'][node]['pvderScale']
					 QNominal = 0 * myconfig['DERParameters']['PVPlacement'][node]['pvderScale']
			elif myconfig['DERSetting'] == 'default':
				 lowSideV = myconfig['DERParameters']['default']['VrmsRating'] 
				 
				 if initializeWithActual:
					 PNominal = (DERRatingReal/1e3)*myconfig['DERParameters']['default']['pvderScale']
					 QNominal = (DERRatingImag/1e3)*myconfig['DERParameters']['default']['pvderScale']
				 else:
					 PNominal = myconfig['DERParameters']['default']['powerRating']*\
					 myconfig['DERParameters']['default']['pvderScale']
					 QNominal = 0 * myconfig['DERParameters']['default']['pvderScale']
		
			OpenDSSData.data['DNet']['DER']['PVDERData']['lowSideV'][node] = lowSideV
			OpenDSSData.data['DNet']['DER']['PVDERData']['PNominal'][node] = PNominal
			OpenDSSData.data['DNet']['DER']['PVDERData']['QNominal'][node] = QNominal
		except:
			OpenDSSData.log()

#===================================================================================================
	def funcval(self,t,y,nEqs=23):
		try:
			fvalue=[]
			for n in range(len(self.pvIDIndex)):
				nEqs = self._nEqs[self.pvIDIndex[n]]
				#fvalue.extend(self._pvders[self.pvIDIndex[n]]._pvderModel.sim.ODE_model(
				#y[n*nEqs:(n+1)*nEqs],t))
				fvalue.extend(self._pvders[self.pvIDIndex[n]]._pvderModel.sim.ODE_model(
				y[n*nEqs:(n+1)*nEqs],t))
			return fvalue
		except:
			OpenDSSData.log()

#===================================================================================================
	def jac(self,t,y,nEqs=23):
		try:
			nPVDER=len(self.pvIDIndex)
			nEqs = self._nEqs[0]
			J=np.zeros((nPVDER*nEqs,nPVDER*nEqs))# zero out at every call to avoid stray values
			for n in range(nPVDER):
				nEqs = self._nEqs[self.pvIDIndex[n]]
				thisJ=self._pvders[self.pvIDIndex[n]]._pvderModel.sim.jac_ODE_model(y,t)
				row,col=np.where(thisJ)
				J[n*nEqs+row,n*nEqs+col]=thisJ[thisJ!=0]
			return J
		except:
			OpenDSSData.log()

#===================================================================================================
	def run(self, V,nEqs=23,dt=1/120.):
		try:
			P = {}
			Q = {}
			# prerun for all pvder instances at this node
			for node in OpenDSSData.data['DNet']['DER']['PVDERMap']:# compute solar inj at each node
				lowSideNode='{}_tfr'.format(node)
				Va = V[lowSideNode]['a']
				Vb = V[lowSideNode]['b']
				Vc = V[lowSideNode]['c']

				for pv in OpenDSSData.data['DNet']['DER']['PVDERMap'][node]:
					if pv!='nSolar_at_this_node':
						pvID=OpenDSSData.data['DNet']['DER']['PVDERMap'][node][pv]
						thisPV=self._pvders[pvID]
						thisPV.prerun(Va,Vb,Vc)

			# single large integrator for all pvder instances
			y=self.integrator.integrate(self.integrator.t+dt)

			# postrun for all pvder instances
			for node in OpenDSSData.data['DNet']['DER']['PVDERMap']:# compute solar inj at each node
				sP=0; sQ=0
				for pv in OpenDSSData.data['DNet']['DER']['PVDERMap'][node]:
					if pv!='nSolar_at_this_node':
						pvID=OpenDSSData.data['DNet']['DER']['PVDERMap'][node][pv]
						assert pvID in self.pvIDIndex, "pvID not found in self.pvIDIndex"
						nEqs = self._nEqs[pvID]
						thisPV=self._pvders[pvID]
						n=self.pvIDIndex.index(pvID)
						sol=np.append(thisPV._pvderModel.lastSol,y[n*nEqs:(n+1)*nEqs])
						sol=sol.reshape((-1,nEqs))
						val=thisPV.postrun(sol,[self.integrator.t-dt,self.integrator.t])
						sP-=val.real# -ve load => generation
						sQ-=val.imag
				P[node] = sP
				Q[node] = sQ
				OpenDSSData.data['DNet']['DER']['PVDERData'][node]['Vmag']['a']=Va
				OpenDSSData.data['DNet']['DER']['PVDERData'][node]['Vmag']['b']=Vb
				OpenDSSData.data['DNet']['DER']['PVDERData'][node]['Vmag']['c']=Vc

			return P, Q
		except:
			OpenDSSData.log(msg="Failed run the pvder aggregated model")


