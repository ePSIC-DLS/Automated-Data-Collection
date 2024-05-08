# -*- coding: utf-8 -*-

from enum import Enum


class _F1Object:
    class F1Kind(Enum):
        trackball=0,
        switch=1,
        command=2,

    class F1Mode(Enum):
        motor=0,
        piezo=1
        
    def __init__(self, default):
        self.table = []
        for kind in self.F1Kind:
            sub = []
            for mode in self.F1Mode:
                sub.append(default)
            self.table.append(sub)
                
                
    def set_value(self, kind, mode, *args):
        self.table[kind][mode] = args
        


class _AccelAndDclrRate:
    class Axis(Enum):
        z=0,
        tx=1,
        ty=2 
        
    def __init__(self):
        self.table = []
        for axis in self.Axis:
            self.table.append([64,64])

    def set_value(self, axis, *param):
        self.table[axis] = param
    

class Stage3:
    _ins = None
    def __init__(self):
        self.__position = [0.0,0.0,0.0,0.0,0.0]   #[x,y,z,tx,ty]
        self.__piezoposi = [0.0,0.0]
        self.__direction = [0,0,0,0,0]
        self.__drvmode = 0    # 0:Motor, 1:Piezo
        self.__holderstate = 0
        self.__stagestatus = [0,0,0,0,0]
        self.__tilt_range = [-90.0, 90.0]
        self.__motor_range = [-100000.0, 100000.0]
        self.__piezo_range = [-10000.00, 10000.00]

        self.__f1default = [0] * 5 # [kind, mode, x,y,z,tx,ty]
        
        self.__f1obj = _F1Object(self.__f1default)
        self.__accelanddclrate =  _AccelAndDclrRate()
        self.__MovementValueMeasurementMethod = 0
        
        self.__Setf1OverRateTxNum = 0
        
    def __new__(cls):
        if cls._ins == None:
            cls._ins = super().__new__(cls)
        return cls._ins

    def GetDirection(self):
        '''
        Summary:
            Get driving direction. 0:-direction, 1:+direction
        
        Return: list
            * [0]= int: X
            * [1]= int: Y
            * [2]= int: Z
            * [3]= int: TiltX
            * [4]= int: TiltY
        '''
        return self.__direction 
        
    def GetDrvMode(self):
        '''
        Summary:
            Get selection on motor/piezo.
        
        Return: int
            0=Motor, 1=Piezo
        '''
        return self.__drvmode
        
    def GetHolderStts(self):
        '''
        Summary:
            Get holder status(inserted or not).
        
        Return: int
            0=OUT, 1=IN
        '''
        return self.__holderstate
 
    def GetPiezoPosi(self):
        '''
        Summary:
            Get piezo position. 
        
        Return: list
            * [0]= float: X Range:+-100000.0(nm)
            * [1]= float: Y Range:+-10000.00(nm) 
        '''
        return self.__piezoposi 
        
    def GetPos(self):
        '''
        Summary:
            Get motor position. 
        
        Return: list
            * [0]= float: X Range:+-100000.0(nm)
            * [1]= float: Y Range:+-100000.0(nm)
            * [2]= float: Z Range:+-100000.0(nm)
            * [3]= float: TiltX Range:+-90.00(degree)
            * [4]= float: TiltY Range:+-180.00(degree)
        '''
        return self.__position
        
    def GetStatus(self):
        '''
        Summary:
            Get driving status. 
        
        Return: list (0=Rest, 1=Moving, 2=Hardware limiter error.)
            * [0]->int: X
            * [1]->int: Y
            * [2]->int: Z
            * [3]->int: TiltX
            * [4]->int: TiltY
        '''
        return self.__stagestatus
        
    def SelDrvMode(self, sw):
        '''
        Summary:
            Select motor/piezo.
        
        Args:
            sw: 
                0=Motor, 1=Piezo
        '''
        if (type(sw) is int):
            if(sw == 0 or sw == 1):
                self.__drvmode = sw
        return 
    
    def SetOrg(self):
        #動作が分からないため未実装
        '''
        Summary:
            Move to origin. Moving order: TiltY, TiltX, X, Z, Y
        
        '''
        return 
        
    def SetPosition(self, x, y):
        '''
        Summary:
            Set X-Y axis drive(with rotation compensation).
            Relative movement from current location.
        
        Args:
            x: 
                Range:+-100000.0(nm)
            y: 
                Range:+-100000.0(nm)
        '''
        if(type(x) is int):
            x = float(x)
        if(type(y) is int):
            y = float(y)
        if(type(x) is float and type(y) is float):
            self.__position[0] = self.__position[0] + x
            self.__position[1] = self.__position[1] + y
            
            self.__direction[0] = _direction(self.__position[0])
            self.__direction[1] = _direction(self.__position[1])
        return            

    def SetX(self, value):
        '''
        Summary:
            Set X axis drive. Absolute amount movement.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__drvmode == 0):
                if(self.__motor_range[0] <= value and value <= self.__motor_range[1]):
                    self.__position[0] = value
                    self.__direction[0] = _direction(self.__position[0])

            elif(self.__drvmode == 1):
                if(self.__piezo_range[0] <= value and value <= self.__piezo_range[1]):
                    self.__piezoposi[0] = value
                    self.__direction[0] = _direction(self.__piezoposi[0])

        return 
        
    def SetY(self, value):
        '''
        Summary:
            Set Y axis drive. Absolute amount movement.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__drvmode == 0):
                if(self.__motor_range[0] <= value and value <= self.__motor_range[1]):
                    self.__position[1] = value
                    self.__direction[1] = _direction(self.__position[1])
            elif(self.__drvmode == 1):
                if(self.__piezo_range[0] <= value and value <= self.__piezo_range[1]):
                    self.__piezoposi[1] = value
                    self.__direction[1] = _direction(self.__piezoposi[1])
        return    
        
    def SetZ(self, value):
        '''
        Summary:
            Set Z axis drive. Absolute amount movement.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__motor_range[0] <= value and value <= self.__motor_range[1]):
                self.__position[2] = value
                self.__direction[2] = _direction(self.__position[2])
        return             
    
    def SetTiltXAngle(self, value):
        '''
        Summary:
            Set TiltX. Absolute amount movement.
        
        Args:
            value: 
                +-90.00 (degree)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__tilt_range[0] <= value and value <= self.__tilt_range[1]):
                self.__position[3] = value
                self.__direction[3] = _direction(self.__position[3])
        return 
        
    def SetTiltYAngle(self, value):
        '''
        Summary:
            Set TiltY. Absolute amount movement.
        
        Args:
            value: 
                +-90.00 (degree)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__tilt_range[0] <= value and value <= self.__tilt_range[1]):
                self.__position[4] = value
                self.__direction[4] = _direction(self.__position[4])
        return    
                                            
    def SetXRel(self, value):
        '''
        Summary:
            Relative move along X axis.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__drvmode == 0):
                temp_value = self.__position[0] + value
                if(self.__motor_range[0] <= temp_value and temp_value <= self.__motor_range[1]):
                    self.__position[0] = temp_value
                    self.__direction[0] = _direction(self.__position[0])
            elif(self.__drvmode == 1):
                temp_value = self.__piezoposi[0] + value
                if(self.__piezo_range[0] <= temp_value and temp_value <= self.__piezo_range[1]):
                    self.__piezoposi[0] = temp_value                
                    self.__direction[0] = _direction(self.__piezoposi[0])
        return 
         
    def SetYRel(self, value):
        '''
        Summary:
            Relative move along Y axis.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            if(self.__drvmode == 0):
                temp_value = self.__position[1] + value
                if(self.__motor_range[0] <= temp_value and temp_value <= self.__motor_range[1]):
                    self.__position[1] = temp_value
                    self.__direction[1] = _direction(self.__position[1])
            elif(self.__drvmode == 1):
                temp_value = self.__piezoposi[1] + value
                if(self.__piezo_range[0] <= temp_value and temp_value <= self.__piezo_range[1]):
                    self.__piezoposi[1] = temp_value                
                    self.__direction[1] = _direction(self.__piezoposi[1])
        return 
         
    def SetZRel(self, value):
        '''
        Summary:
            Relative move along Z axis.
        
        Args:
            value: 
                * For motor drive Range: +-100000.0(nm)
                * For piezo Range: +-10000.00(nm)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            temp_value = self.__position[2] + value
            if(self.__motor_range[0] <= temp_value and temp_value <= self.__motor_range[1]):
                self.__position[2] = temp_value
                self.__direction[2] = _direction(self.__position[2])
        return 
               
    def SetTXRel(self, value):
        '''
        Summary:
            Relative tilt around TiltX.
        
        Args:
            value: 
                +-90.00 (degree)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            temp_value = self.__position[3] + value
            if(self.__tilt_range[0] <= temp_value and temp_value <= self.__tilt_range[1]):
                self.__position[3] = temp_value
                self.__direction[3] = _direction(self.__position[3])
        return 
                 
    def SetTYRel(self, value):
        '''
        Summary:
            Relative tilt around TiltY.
        
        Args:
            value: 
                +-90.00 (degree)
        '''
        if(type(value) is int):
            value = float(value)
        if(type(value) is float):
            temp_value = self.__position[4] + value
            if(self.__tilt_range[0] <= temp_value and temp_value <= self.__tilt_range[1]):
                self.__position[4] = temp_value
                self.__direction[4] = _direction(self.__position[4])
        return 
        
    def Stop(self):
        '''
        Summary:
            Stop all the drives.
        '''
        self.__stagestatus = [0,0,0,0,0]
        return
        
## Ver.1.2
    def Setf1OverRate(self, kind , mode, x, y, z, tx, ty):
        """
        Summary:
            Drive frequency f1 setting.
        Args:
            kind: 0:trackbaul, 1:sw, 2:command
            mode: 0:motor, 1:piezo
            x: x (drive frequency value)
            y: y (drive frequency value)
            z: z (drive frequency value)
            tx: tx (drive frequency value)
            ty: ty (drive frequency value)
        """
        self.__f1obj.set_value(kind, mode, x,y,z,tx,ty) 
        return 
    
    def Getf1OverRate(self, kind , mode):
        """
        Summary:
            Get drive frequency f1.
        Args:
            kind: 0:trackbaul, 1:sw, 2:command
            mode: 0:motor, 1:piezo
        Return -> list
            [0]: x (drive frequency value)
            [1]: y (drive frequency value)
            [2]: z (drive frequency value)
            [3]: tx (drive frequency value)
            [4]: ty (drive frequency value)
        """
        return self.__f1obj
    
    def SetMovementValueMeasurementMethod(self, kind):
        """
        Summary:
            Movement amount measurement method setting(for Z/Tx/Ty).
        Args:
            kind : -> int 
                0:encoder
                1:potens
        """
        self.__MovementValueMeasurementMethod = kind
        return 
    
    def GetMovementValueMeasurementMethod(self):
        """
        Summary:
            Get movement amount measurement method (for Z/Tx/Ty).
        Return: -> int
            0:encoder, 1:potens
        """
        return self.__MovementValueMeasurementMethod 
    
    def SetAccelAndDclrRate(self, axis, accel, decel):
        """
        Summary:
            Acceleration / decelerateion rate setting during keystone control (for Z/Tx/Ty).
        Args:
            axis: -> int
                2:Z axis
                3:Tx axis
                4:Ty axis, 
            accel: -> int
                64-65535
            decel: -> int
                64-65535
        """
        self.__accelanddclrate.set_value(axis, accel, decel)
        return 
    
    def GetAccelAndDclrRate(self):
        """
        Summary:
            Get acceleration / decelerateion rate during keystone control (for Z/Tx/Ty).
        Args:
            axis: -> int
                2:Z axis
                3:Tx axis
                4:Ty axis, 
        Return: -> list
            [0]: accel: 64-65535
            [1]: decel: 64-65535
        """
        return self.__accelanddclrate.table
        
    def Setf1OverRateTxNum(self,tx):
        """
        Summray:
            Drive frequency f1 setting of TiltX.
            This function only work on Cryo-ARM.
            * Only when electron beam 3D crystallography kit is enabled
        Args:
            tx: -> int
                0: 10(/sec)
                1: 2(/sec)
                2: 1(/sec)
                3: 0.5(/sec). 
        """
        self.__Setf1OverRateTxNum = tx
        return 
        
    def Getf1OverRateTxNum(self):
        """
        Summray:
            Get drive frequency f1 of TiltX.
            This function only work on Cryo-ARM.
            * Only when electron beam 3D crystallography kit is enabled
        Return: -> int
            0: 10(/sec)
            1: 2(/sec)
            2: 1(/sec)
            3: 0.5(/sec). 
        """
        return self.__Setf1OverRateTxNum
        
        
def _direction(value):
    if(value > 0):
        return 1
    else:
        return 0
        
    
