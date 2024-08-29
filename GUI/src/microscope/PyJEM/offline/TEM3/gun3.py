# -*- coding: utf-8 -*-




class GUN3:
    def __init__(self):
        self.__a1_value = 0.0
        self.__a2_value = 0.0
        self.__beam_sw = 0
        self.__emission_value = 0.0
        self.__filament_cur_value = 0.0
        self.__filament_value = 0.0
        self.__ht_status = 0
        
        # target
        self.__target = []
        self.__target.append(0) # ht
        self.__target.append(0) # anode1
        self.__target.append(0) # anode2
        self.__target.append(0) # bias
        self.__target.append(0) # filament
        self.__target.append(0) # energyshift 

        # monitor
        self.__monior = []
        self.__monior.append(0) # dark
        self.__monior.append(0) # emission
        self.__monior.append(0) # anode1
        self.__monior.append(0) # anode2
        self.__monior.append(0) # bias
        self.__monior.append(0) # filament
        
        # monitor
        self.__current = []
        self.__current.append(0) # ht
        self.__current.append(0) # anode1
        self.__current.append(0) # anode2
        self.__current.append(0) # bias
        self.__current.append(0) # dark
        self.__current.append(0) # energyshift
        self.__current.append(0) # emission
        
        self.__htwobbler_sw = 0
    
    def GetAnode1CurrentValue(self):
        '''
        Summary:
            Get Anode1 current value(kV). 
                * This works for FEG.
        
        Return: int
            A1 value
        '''
        return self.__a1_value 
        
    def GetAnode2CurrentValue(self):
        '''
        Summary:
            Get Anode2 current value(kV). 
                * This works for FEG.

        Return: int
            A2 value.
        '''
        return self.__a2_value
        
    def GetBeamSw(self):
        '''
        Summary:
            Get beam switch status. 
                * This does not work for FEG.

        Return: int
            0=OFF, 1=ON 
        '''
        return self.__beam_sw
        
    def GetEmissionCurrentValue(self):
        '''
        Summary:
            Get emission current value(uA).This works for FEG.

        Return: int
            emission current value
        '''
        return self.__emission_value 
        
    def GetFilamentCurrentValue(self):
        '''
        Summary:
            Get emission current value(uA). This works for FEG.

        Return: int
            filament current value.
        '''
        return self.__filament_cur_value
        
    def GetFilamentVal(self):
        '''
        Summary:
            Get filment current value. This does not work for FEG.

        Return: float
            filament value.
        '''
        return self.__filament_value
  
    def GetHtStts(self):
        '''
        Summary:
            Get HT status. This does not work for FEG.

        Return: float
            0=OFF, 1=ON, 2=Increasing or Decreasing
        '''
        return self.__ht_status
        
    def SetBeamSw(self, sw):
        '''
        Summary:
            Set beam switch. Start heating filament. This does not work for FEG.

        Args:
            sw: int
                0=OFF, 1=ON
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__beam_sw = sw
        return 

    def SetFilamentVal(self, value):
        '''
        Summary:
            Set filment current value. This does not work for FEG.

        Args:
            value: float
                filament value. range(0-4.095)
        '''
        if (type(value) is int):
            value = float(value)
        if(type(value) is float):
            self.__filament_value = value
#            self.__filament_cur_value = value
        return 
                
    def GetHtTargetValue(self):
        """
        Summary:        
            Get the HT-related target values.
        Args: 
            no argument.
        Return: list((int)ht, (int)a1, (int)a2, (int)bias, (int)fil, (int)es)
            * ht-> target ht value.
            * a1-> target anode1 value.
            * a2-> target anode2 value.
            * bias-> target bias value.
            * fil-> target filament value.
            * es-> target energy shift value.
        """
        return self.__target

    def GetHtMonitorValue(self):
        """
        Summary:        
            Get the HT-related monitor values.
        Args: 
            no argument.
        Return: list((int)dark, (int)emi, (int)a1, (int)a2, (int)bias, (int)fil)
            * dark-> moinitor dark value.
            * emi-> moinitor emission shift value.
            * a1-> moinitor anode1 value.
            * a2-> moinitor anode2 value.
            * bias-> moinitor bias value.
            * fil-> moinitor filament value.
        """
        return self.__monior

    def GetHtCurrentValue(self):
        """
        Summary:        
            Get the HT-related current values.
        Args: 
            no argument.
        Return: list((int)ht, (int)a1, (int)a2, (int)bias, (int)fil, (int)es, (int)dark, (int)emi)
            * ht-> current ht value.
            * a1-> current anode1 value.
            * a2-> current anode2 value.
            * bias-> current bias value.
            * fil-> current filament value.
            * es-> current energy shift value.
            * dark-> current dark value.
            * emi-> current emission value.
        """
        return self.__current
    
    
## Ver.1.2
 
    def SetHtWobbler(self, sw):
        """
        Summary:
            Execute Ht wobbler. 
        Args:     
            0:OFF, 1:ON
        """
        self.__htwobbler_sw = sw
        return 
    
    def SetA2Wobbler(self, sw):
        """
        Summary:
            Execute Ht wobbler. 
            * This works for FEG.
        Args:     
            0:OFF, 1:ON
        """
        self.__a2wobbler_sw = sw
        return 
    
    def SetA2Rel(self, value):        
        """
        Summary:
            Set A2 value. 
        Args:
            value: -> int            
                unit is 10V 
        * This works for FEG.
        """
        self.__a2_value + value
        return 
    
    def SetA2Abs(self, value):
        """
        Summary:
            Set A2 value. 
        Args:
            value: -> int            
                unit is 10V 
        * This works for FEG.
        """
        self.__a2_value =value
        return 
    
    def SetHtStts(self, value):
        """
        Summary:
            Change HT on/off switch.
        Args:
            sw: -> int
                0=OFF, 
                1=ON, 
                2=Increasing or Decreasing
        """
        self.__ht_status =value
        return
    
    
    
   
    
