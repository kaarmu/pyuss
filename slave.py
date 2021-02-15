"""

USS Protocol
============

[Telegram] = {STX} {LGE} {ADR} [Net Data Block] {BCC}
    {STX}: (1B) = '\x02'
    {LGE}: Telegram length, except STX and LGE (1B)
    {ADR}: Slave address (1B) = {Special} {Mirror} {Broadcast} {Slave No}
        {Special}: (1b)
        {Mirror}: (1b)
        {Broadcast}: (1b)
        {Slave No}: (5b)
    {BCC}: Checksum (1B) 

[Net Data Block] = [PKW Area] [PZD Area]
    [PKW Area] = {PKE} {IND} [PWE Elements]
        {PKE}: (2B) = {AK} {SP} {PNU}
            {AK}: Task and Response ID (4b)
            {SP}: Change report (1b)
            {PNU}: Parameter No (11b)
        {IND}: (2B) = {High byte} {RW} {Low byte}
            {High byte}: Drive converter-specific (6b)
            {RW}: Read/Write Textextension (2b)
            {Low byte}: (1B)
        [PWE Elements] = {PWE1} {PWE2} ... {PWEn}
            {PWEx}: Parameter value (2B)
    [PZD Area] = {PZD1} {PZD2} ... {PZDm}
        {PZDx}: Process data value (2B)


Parameter Process data Object (PPO) types
-----------------------------------------
Ex.

PPO1 = {PKE} {IND} {PWE1} {PWE2} {PZD1} {PZD2}
PPO2 = {PKE} {IND} {PWE1} {PWE2} {PZD1} {PZD2} {PZD3} {PZD4}
PPO3 =                           {PZD1} {PZD2}
PPO4 =                           {PZD1} {PZD2} {PZD3} {PZD4}


"""

from serial import Serial

TASK_ID = {
    0b0000: "No task",
    0b0001: "Request PWE",
    0b0010: "Change PWE (word)",
    0b0011: "Change PWE (double word)",
    0b0100: "Request PBE element 1)",
    0b0101: "Change PBE element 1)",
    0b0110: "Request PWE (array) 1)", 
    0b0111: "Change PWE (array word) 1)",
    0b1000: "Change PWE (array double word) 1)",
    0b1001: "Request the number of array elements",
    0b1010: "Reserved",
    0b1011: "Change PWE (array double word), and storein the EEPROM 1), 2)",
    0b1100: "Change PWE (array word), and store in theEEPROM 1), 2)",
    0b1101: "Change PWE (double word), and store inEEPROM 2)",
    0b1110: "Change PWE (word), and store in theEEPROM 2)",
    0b1111: "Request or change text 1), 2) 3)",
}



class Slave:

    def __init__(self, ser: Serial, slaveno: int) -> None:
        self.ser = ser

        assert slaveno < (1 << 5), f'Slave number cant be {1 << 5} or greater.'
        self.slaveno = slaveno

    def send(self, netData: bytes, *, special: bool = False,
             mirror: bool = False, broadcast: bool = False) -> None:
        """
        Create a frame and send data.

        Args
        ----
        

        """        
        stx = b'\x02'

        assert len(netData) <= 252, 'Too big payload.'
        lge = bytes([len(netData) + 2])
        
        adr = self.slaveno
        if broadcast: adr |= 1 << 5
        if mirror   : adr |= 1 << 6
        if special  : adr |= 1 << 7
        
        bcc = stx ^ lge ^ adr
        for byte in netData:
            bcc ^= byte

        self.ser.write(stx + lge + netData + bcc)

    def _createPKW(self, ak: int, paramno: int, index: int, pwes: bytes, *, sp: bool = False):
        """
        Create the PKW Area.
        
        [PKW Area] = {PKE} {IND} [PWE Elements]
            {PKE}: (2B) = {AK} {SP} {PNU}
                {AK}: Task and Response ID (4b)
                {SP}: Change report (1b)
                {PNU}: Parameter No (11b)
            {IND}: (2B) = {High byte} {RW} {Low byte}
                {High byte}: Drive converter-specific (6b)
                {RW}: Read/Write Textextension (2b)
                {Low byte}: (1B)
            [PWE Elements] = {PWE1} {PWE2} ... {PWEn}
                {PWEx}: Parameter value (2B)

        """
        assert ak in TASK_ID, 'Invalid AK'
        assert paramno.bit_length() <= 11, b'PNU cannot be greater than {1 << 11}'
        
        pke = ak << 1
        if sp: pke |= 1
        pke <<= 11
        pke |= paramno


    
    def _createPZD(self):
        """
        Create the PZD Area.
        
        [PZD Area] = {PZD1} {PZD2} ... {PZDm}
            {PZDx}: Process data value (2B)

        """
        
