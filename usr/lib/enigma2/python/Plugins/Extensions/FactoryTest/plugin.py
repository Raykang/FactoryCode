from Components.About import about
from Components.ActionMap import ActionMap, NumberActionMap
from Components.config import config, ConfigSubsection, ConfigNothing, ConfigSelection, ConfigSatlist, ConfigSubDict, ConfigYesNo, ConfigInteger, ConfigOnOff, ConfigSlider
from Components.Console import Console
from Components.Label import Label, MultiColorLabel
from Components.MenuList import MenuList
from Components.NimManager import InitNimManager, nimmanager
from Components.ScrollLabel import ScrollLabel
from Components.Sources.FrontendStatus import FrontendStatus
from Components.TunerInfo import TunerInfo
from Components.ServiceEventTracker import ServiceEventTracker
from Tools.Directories import fileExists
from enigma import eDVBCIInterfaces, eDVBResourceManager, eServiceReference, eSize, eTimer, getDesktop, eAVSwitch, eDVBDB, iPlayableService, eDVBFrontendParametersSatellite, eDVBFrontendParametersCable, eDVBFrontendParametersTerrestrial, eDVBFrontendParameters, eDVBServicePMTHandler, iServiceInformation, iRecordableService
from Plugins.Plugin import PluginDescriptor
from Screens.Screen import Screen
from Screens.NetworkSetup import NetworkAdapterSelection
import xml.dom.minidom
from ctypes import cdll
import os
g_timerinstance = None
g_session = None
advanced_lnb_csw_choices = [('none', _('None')),
 ('AA', _('AA')),
 ('AB', _('AB')),
 ('BA', _('BA')),
 ('BB', _('BB'))]
advanced_lnb_csw_choices += [ (str(240 | y), 'Input ' + str(y + 1)) for y in range(0, 16) ]
advanced_lnb_ucsw_choices = [('0', _('None'))] + [ (str(y), 'Input ' + str(y)) for y in range(1, 17) ]
advanced_lnb_choices = [('0', 'not available')] + [ (str(y), 'LNB ' + str(y)) for y in range(1, 33) ]
advanced_voltage_choices = [('polarization', _('Polarization')), ('13V', _('13 V')), ('18V', _('18 V'))]
advanced_tonemode_choices = [('band', _('Band')), ('on', _('On')), ('off', _('Off'))]
advanced_lnb_toneburst_choices = [('none', _('None')), ('A', _('A')), ('B', _('B'))]
advanced_lnb_allsat_diseqcmode_choices = [('1_2', _('1.2'))]
advanced_lnb_diseqcmode_choices = [('none', _('None')),
 ('1_0', _('1.0')),
 ('1_1', _('1.1')),
 ('1_2', _('1.2'))]
advanced_lnb_commandOrder1_0_choices = [('ct', 'committed, toneburst'), ('tc', 'toneburst, committed')]
advanced_lnb_commandOrder_choices = [('ct', 'committed, toneburst'),
 ('tc', 'toneburst, committed'),
 ('cut', 'committed, uncommitted, toneburst'),
 ('tcu', 'toneburst, committed, uncommitted'),
 ('uct', 'uncommitted, committed, toneburst'),
 ('tuc', 'toneburst, uncommitted, commmitted')]
advanced_lnb_diseqc_repeat_choices = [('none', _('None')),
 ('one', _('One')),
 ('two', _('Two')),
 ('three', _('Three'))]
prio_list = [('-1', _('Auto'))]
prio_list += [ (str(prio), str(prio)) for prio in range(65) + range(14000, 14065) + range(19000, 19065) ]
lnb_choices = {'universal_lnb': _('Universal LNB'),
 'unicable': _('Unicable'),
 'c_band': _('C-Band'),
 'user_defined': _('User defined')}
models = ['g300', 'et10000', 'et8000', 'et9x00', 'et7500', 'et7000', 'et8500', '7000S', '7100S', '7200S', '7300S', '7400S', '7210S', '7220S', '7005S', '7105S', '7205S', '7305S', '7405S', '7215S', '7225S', '8100S', 'e4hd', 'protek4k', 'hd61']
JIG_VERSION = '1.0'

class cFactoryTestPlugin(Screen):
    TEST_NONE = 0
    TEST_KEYS = 1
    TEST_HDMI_IN = 2
    TEST_AGING = 3
    TEST_TUNER = 4
    TEST_REMOVE = 5
    TEST_ESATA = 6
    TEST_SATA = 7
    TEST_SCART = 8
    TEST_HDD = 9
    TEST_FRONT_LED = 10
    locations = []
    recordTestFileName = '/media/hdd/record_test.ts'

    def __init__(self, session):
        if os.path.exists('/proc/stb/info/boxtype'):
            self.boxtype = self.readFile('/proc/stb/info/boxtype')
            if self.boxtype not in models:
                os._exit(1)
        else:
            os._exit(1)
        if self.boxtype == 'et10000' or self.boxtype == 'et8000':
            if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/factoryhelper.so'):
                self.dll = cdll.LoadLibrary('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/factoryhelper.so')
            else:
                os._exit(1)
        if os.path.exists('/proc/stb/info/board_revision'):
            if self.boxtype == 'et9x00' or self.boxtype == 'et7500' or self.boxtype == 'et7000' or self.boxtype == 'et8500' or self.boxtype == 'g300':
                self.hardwareversion = self.readFile('/proc/stb/info/board_revision')
            elif self.boxtype == '7000S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7210S' or self.boxtype == '7220S':
                self.hardwareversion = self.readFile('/proc/stb/info/board_revision')
            elif self.boxtype == '7005S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7215S' or self.boxtype == '7225S':
                self.hardwareversion = self.readFile('/proc/stb/info/board_revision')
            elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                self.hardwareversion = self.readFile('/proc/stb/info/board_revision')
            else:
                self.hardwareversion = '0.' + self.readFile('/proc/stb/info/board_revision')
        else:
            os._exit(1)
        if self.boxtype == 'et10000' or self.boxtype == 'et8000' or self.boxtype == 'et8500':
            if os.path.exists('/proc/stb/fp/fan'):
                self.fanControl('on')
        if self.boxtype == 'et10000':
            self.tuners = [['Unknown', 'Unknown'],
             ['Unknown', 'Unknown'],
             ['Unknown', 'Unknown'],
             ['Unknown', 'Unknown']]
            self.usbslot_names = ['Back Left Low',
             'Back Left High',
             'Back Right Low',
             'Back Right High',
             'Front']
            self.usbslot_target = ['3-1.4',
             '3-1.3',
             '1-',
             '2-',
             '4-']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'Tuner 3',
             'Tuner 4',
             'HDD Test',
             'Scart Test',
             'HDMI IN Test',
             'Front Panel Test',
             'Front LED Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 4)
            self.button_count = 8
            self.buttons = {'menu': 6,
             'cancel': 7,
             'power': 0,
             'volup': 2,
             'voldown': 1,
             'left': 3,
             'right': 4,
             'up': 5,
             'down': 4,
             'ok': 3}
            self.has_esata = True
            self.has_security = True
        elif self.boxtype == 'g300':
            self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Back Low', 'Back High', 'Front']
            self.usbslot_target = ['1-', '2-', '3-']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'Tuner 3',
             'FRONT KEY TEST',
             'FRONT VFD TEST',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 3)
            self.button_count = 1
            self.buttons = {'menu': 6,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = True
            self.has_esata = True
            self.has_security = False
        elif self.boxtype == 'et8000':
            self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Back Low', 'Back High', 'Front']
            self.usbslot_target = ['1-', '2-', '3-']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'Tuner 3',
             'HDD Test',
             'Scart Test',
             'Front Panel Test',
             'Front LED Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 3)
            self.button_count = 8
            self.buttons = {'menu': 6,
             'cancel': 7,
             'power': 0,
             'volup': 2,
             'voldown': 1,
             'left': 3,
             'right': 4,
             'up': 5,
             'down': 4,
             'ok': 3}
            self.has_esata = True
            self.has_security = True
        elif self.boxtype == 'et9x00':
            self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Back Horizontal', 'Back Vertical', 'Front']
            self.usbslot_target = ['1-', '2-', '3-']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'HDD Test',
             'Scart Test',
             'Front Panel Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 2)
            self.button_count = 5
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 2,
             'voldown': 1,
             'left': -1,
             'right': -1,
             'up': 4,
             'down': 3,
             'ok': -1}
            self.has_esata = True
            self.has_security = False
        elif self.boxtype == 'et7000':
            self.tuners = [['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            self.menu_names = ['Tuner 1',
             'Front Panel Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 1)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_esata = True
            self.has_security = False
        elif self.boxtype == '7000S' or self.boxtype == '7005S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown']]
            self.usbslot_names = ['Rear1', 'Rear2']
            self.usbslot_target = ['1-1', '1-2']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 2)
            else:
                self.menu_tuner_index = range(0, 1)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'channelup': -1,
             'channeldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '7100S' or self.boxtype == '7105S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 3)
            else:
                self.menu_tuner_index = range(0, 2)
            self.button_count = 5
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 3,
             'voldown': 4,
             'channelup': 1,
             'channeldown': 2,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '7200S' or self.boxtype == '7205S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 3)
            else:
                self.menu_tuner_index = range(0, 2)
            self.button_count = 5
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 3,
             'voldown': 4,
             'channelup': 1,
             'channeldown': 2,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '7210S' or self.boxtype == '7215S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 '0-5V',
                 'Scart Test',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Scart Test',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 3)
            else:
                self.menu_tuner_index = range(0, 2)
            self.button_count = 5
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 3,
             'voldown': 4,
             'channelup': 1,
             'channeldown': 2,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '7220S' or self.boxtype == '7225S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 3)
            else:
                self.menu_tuner_index = range(0, 2)
            self.button_count = 6
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 4,
             'voldown': 5,
             'channelup': 2,
             'channeldown': 3,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': 1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown']]
            self.usbslot_names = ['Side', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 2)
            else:
                self.menu_tuner_index = range(0, 1)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'channelup': -1,
             'channeldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Side', 'Rear']
            self.usbslot_target = ['2-1.1', '1-1']
            self.usbslot_target2 = ['2-1.1', '6-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Tuner 3',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Tuner 3',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 4)
            else:
                self.menu_tuner_index = range(0, 3)
            self.button_count = 5
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': 4,
             'voldown': 3,
             'channelup': -1,
             'channeldown': -1,
             'left': 1,
             'right': 2,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = False
            self.has_esata = False
            self.has_security = False
        elif self.boxtype == 'hd61':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            else:
                self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['3-1', '1-1']
            self.usbslot_target2 = ['3-1', '6-1']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Tuner 3',
                 '0-5V',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            else:
                self.menu_names = ['Tuner 1',
                 'Tuner 2',
                 'Tuner 3',
                 'Front Panel Test',
                 'Front LED Test',
                 'Factory Default']
            if nimmanager.hasNimType("DVB-T2"):
                self.menu_tuner_index = range(0, 4)
            else:
                self.menu_tuner_index = range(0, 3)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'channelup': -1,
             'channeldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_sata = True
            self.has_esata = False
            self.has_sdcard = True
            self.has_security = False
        elif self.boxtype == 'et7500':
            self.tuners = [['Unknown', 'Unknown'], ['Unknown', 'Unknown']]
            self.usbslot_names = ['Front', 'Rear']
            self.usbslot_target = ['1-2', '1-1']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'Front Panel Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 2)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_esata = True
            self.has_security = False
        elif self.boxtype == 'et8500':
            self.tuners = [['Unknown', 'Unknown'],
             ['Unknown', 'Unknown'],
             ['Unknown', 'Unknown'],
             ['Unknown', 'Unknown']]
            self.usbslot_names = ['Rear1',
             'Rear2',
             'Rear3',
             'Side']
            self.usbslot_target = ['3-1',
             '2-1',
             '1-1',
             '4-1']
            self.menu_names = ['Tuner 1',
             'Tuner 2',
             'Tuner 3',
             'Tuner 4',
             'Front Panel Test',
             'Aging Test',
             'Factory Default']
            self.menu_tuner_index = range(0, 4)
            self.button_count = 1
            self.buttons = {'menu': -1,
             'cancel': -1,
             'power': 0,
             'volup': -1,
             'voldown': -1,
             'left': -1,
             'right': -1,
             'up': -1,
             'down': -1,
             'ok': -1}
            self.has_esata = True
            self.has_security = False
        if os.path.exists('/dev/sci1'):
            self.scislots = 2
            self.scislot = [False, False]
        elif os.path.exists('/dev/sci0'):
            self.scislots = 1
            self.scislot = [False]
        else:
            self.scislots = 0
        self.cislots = eDVBCIInterfaces.getInstance().getNumOfSlots()
        if self.boxtype == 'et8500':
            self.cislots = 1
        if self.cislots > 1:
            self.cislot = [False, False]
        else:
            self.cislot = [False]
        if os.path.exists('/sys/class/net/eth1'):
            self.has_eth1 = True
            os.system('ifup eth1')
        else:
            self.has_eth1 = False
        self.usbslots = len(self.usbslot_target)
        self.usbslot = []
        self.usbslot_target_found = []
        self.last_message_size = []
        for x in range(self.usbslots):
            self.usbslot_target_found.append(False)
            self.usbslot.append(False)
            self.last_message_size.append(0)

        self.skin = '<screen position="0,0" size="e-0,e-0" title="Factory Test" flags="wfNoBorder" backgroundColor="transparent">'
        leftindex = 0
        voffset = 40
        self.total_left = len(self.menu_names)
        for x in range(self.total_left):
            self.skin += '\n\t<widget name="menuleftbox' + str(leftindex) + '" position="68,' + str(voffset) + '" size="270,34" zPosition="10" backgroundColors="#000000,#ff0000" foregroundColors="#FFFFFF,#000000" />'
            self.skin += '\n\t<widget name="menuleft' + str(leftindex) + '" position="70,' + str(voffset + 2) + '" size="266,30" font="Regular;24" zPosition="20" backgroundColors="#0040FF,#F4FA58,#848484" foregroundColors="#FFFFFF,#848484,#000000" />'
            leftindex = leftindex + 1
            voffset = voffset + 34

        self.total_right = self.usbslots + self.scislots + self.cislots + 1
        if self.has_eth1 is True:
            self.total_right = self.total_right + 1
        if self.has_esata is True:
            self.total_right = self.total_right + 1
        if self.has_sata is True:
            self.total_right = self.total_right + 1
        if self.has_sdcard is True:
            self.total_right = self.total_right + 1
        if self.has_security is True:
            self.total_right = self.total_right + 1
        self.last_esata_message_size = 0
        self.last_sdcard_message_size = 0
        print 'self.total_right: %d, self:usbslots: %d, self.scislots: %d, self.cislots: %d' % (self.total_right,
         self.usbslots,
         self.scislots,
         self.cislots)
        self.skin += '\n'
        for x in range(self.total_right):
            self.skin += '\n\t<widget name="menuright' + str(x) + '" position="920,' + str(x * 30 + 40) + '" size="290,28" font="Regular;24" zPosition="10" backgroundColors="#0040FF,#F4FA58" foregroundColors="#FFFFFF,#848484" />'

        self.skin += '\n'
        for x in range(self.button_count):
            if self.boxtype == 'et7000' or self.boxtype == 'et7500' or self.boxtype == 'et8500':
                self.skin += '\n\t<widget name="button' + str(x) + '" position="' + str(x * 35 + 930) + ',400" size="84,84" zPosition="10" backgroundColors="#0040FF,#F4FA58" foregroundColors="#FFFFFF,#0040FF" />'
            else:
                self.skin += '\n\t<widget name="button' + str(x) + '" position="' + str(x * 35 + 930) + ',440" size="28,28" zPosition="10" backgroundColors="#0040FF,#F4FA58" foregroundColors="#FFFFFF,#0040FF" />'

        self.skin += '\n'
        self.skin += '\n\t<widget name="message_header" position="340,159" size="576,322" font="Regular;24" zPosition="10" backgroundColor="#87CEFA" foregroundColor="#000000" halign="center" valign="top" />'
        self.skin += '\n\t<widget name="message" position="342,190" size="572,290" font="Regular;24" zPosition="20" backgroundColor="#0B173B" halign="center" valign="center" />\n\t'
        self.skin += '\n'
        self.skin += '\n\t<widget name="stbname" position="70,470" size="266,40" halign="left" valign="center" font="Regular;22" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
        self.skin += '\n'
        if self.boxtype == 'et8000' or self.boxtype == 'et10000' or self.boxtype == 'et8500' or self.boxtype == 'g300':
            self.skin += '\n\t<widget name="faninfo" position="70,510" size="266,60" halign="left" valign="center" font="Regular;20" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
            self.skin += '\n\t<widget name="tunerinfo" position="70,570" size="266,40" halign="left" valign="center" font="Regular;22" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
        else:
            self.skin += '\n\t<widget name="tunerinfo" position="70,510" size="266,40" halign="left" valign="center" font="Regular;22" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
        self.skin += '\n'
        if self.has_eth1 is True:
            self.skin += '\n\t<widget name="hwinfo" position="920,480" size="290,140" valign="center" font="Regular;20" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
        else:
            self.skin += '\n\t<widget name="hwinfo" position="920,500" size="290,120" valign="center" font="Regular;20" zPosition="10" backgroundColor="#848484" foregroundColor="#000000" />'
        self.skin += '\n'
        for x in range(self.button_count):
            self.skin += '\n\t<widget name="buttons" position="0,625" size="e-0,e-620" font="Regular;24" zPosition="10" backgroundColor="#0B173B" />'

        self.skin += '\n'
        self.skin += '\n\t<ePixmap pixmap="skin_default/buttons/button_red.png" position="70,655" size="30,30" zPosition="10" />'
        self.skin += '\n\t<widget name="buttons_red" position="100,645" size="200,40" font="Regular;24" zPosition="10" backgroundColor="#0B173B" />'
        self.skin += '\n\t<ePixmap pixmap="skin_default/buttons/button_yellow.png" position="330,655" size="30,30" zPosition="10" />'
        self.skin += '\n\t<widget name="buttons_yellow" position="360,645" size="200,40" font="Regular;24" zPosition="20" backgroundColor="#0B173B" />'
        self.skin += '\n'
        self.skin += '\n\t<widget name="buttons_blue" position="658,340" zPosition="20" size="50,24" backgroundColor="#0040FF" />'
        self.skin += '\n'
        self.skin += '\n\t<widget name="version" position="950,645" size="290,40" zPosition="20" backgroundColor="#0B173B" font="Regular;24" />'
        self.skin += '\n</screen>'
        self.session = session
        Screen.__init__(self, session)
        self['actions'] = ActionMap(['DirectionActions',
         'GlobalActions',
         'ColorActions',
         'OkCancelActions',
         'MoviePlayerActions',
         'MovieSelectionActions'], {'ok': self.keyOk,
         'cancel': self.keyCancel,
         'contextMenu': self.keyMenu,
         'up': self.keyUp,
         'down': self.keyDown,
         'left': self.keyLeft,
         'right': self.keyRight,
         'power_down': self.keyPower,
         'power_up': self.keyPower,
         'red': self.keyRed,
         'yellow': self.keyYellow,
         'blue': self.keyBlue,
         'volumeUp': self.keyVolumeUp,
         'volumeDown': self.keyVolumeDown,
         'channelUp': self.keyChannelUp,
         'channelDown': self.keyChannelDown}, -1)
        self['numactions'] = NumberActionMap(['NumberActions'], {'1': self.keyNumberGlobal,
         '2': self.keyNumberGlobal,
         '3': self.keyNumberGlobal,
         '4': self.keyNumberGlobal,
         '5': self.keyNumberGlobal,
         '6': self.keyNumberGlobal,
         '7': self.keyNumberGlobal,
         '8': self.keyNumberGlobal,
         '9': self.keyNumberGlobal,
         '0': self.keyNumberGlobal}, -1)
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evTunedIn: self.evTunedInEvent,
         iPlayableService.evTuneFailed: self.evTuneFailedEvent,
         iPlayableService.evEnd: self.evEndEvent,
         iPlayableService.evEOF: self.evEOFEvent})
        self.want_ok = False
        self.TEST_KEYS = False
        self.type_test = self.TEST_NONE
        self.leftmenu_idx = 0
        self.mac = ''
        self.local_ip_eth0 = '0.0.0.0'
        self.local_ip_eth1 = '0.0.0.0'
        self.location_idx = 0
        self.tune_index = 0
        self.tuner_nr = 0
        self.tuner_count = 0
        self.frontendStatus = {}
        self.lockState = TunerInfo(TunerInfo.LOCK_STATE, statusDict=self.frontendStatus)
        self.tune_text = ''
        self.tune_test_start = False
        self.zapped = False
        self.record = None
        self.record_start = False
        self.record_test_start = False
        self.record_end = False
        self.record_play_start = False
        self.record_time = 5
        self.isExistHDD = False
        self.count = 0
        self.frontend = None
        self.raw_channel = None
        self.scart_type = 0
        self.scart_aspect_ratio = 0
        self.ledtest = False
        self.front_ok_key_idx = 0
        self.runAgingTestKeyActionProtect = False
        for x in range(self.total_left):
            self['menuleft' + str(x)] = MultiColorLabel()
            self['menuleft' + str(x)].setForegroundColorNum(0)
            self['menuleft' + str(x)].setBackgroundColorNum(0)

        for x in range(self.total_left):
            self['menuleftbox' + str(x)] = MultiColorLabel()
            self['menuleftbox' + str(x)].setForegroundColorNum(0)
            self['menuleftbox' + str(x)].setBackgroundColorNum(0)

        for x in range(self.total_right):
            self['menuright' + str(x)] = MultiColorLabel()
            self['menuright' + str(x)].setForegroundColorNum(0)
            self['menuright' + str(x)].setBackgroundColorNum(0)

        for x in range(self.usbslots):
            self.setRightMenuUsb(x, False)

        if self.scislots > 0:
            self.setRightMenuSmartcard(0, False)
        if self.scislots > 1:
            self.setRightMenuSmartcard(1, False)
        self.setRightMenuEthernet(0, False)
        if self.has_eth1 is True:
            self.setRightMenuEthernet(1, False)
        if self.cislots > 0:
            self.setRightMenuCi(0, False)
        if self.cislots > 1:
            self.setRightMenuCi(1, False)
        if self.has_esata is True:
            self.setRightMenuEsata(0)
        if self.has_sata is True:
            self.setRightMenusata(0)
        if self.has_sdcard is True:
            self.setRightMenuSDcard(0)
        for x in range(self.button_count):
            self['button' + str(x)] = MultiColorLabel()
            self['button' + str(x)].setForegroundColorNum(0)

        self['message_header'] = Label('')
        self['message'] = Label('')
        self['stbname'] = Label('')
        self['tunerinfo'] = Label('')
        self['hwinfo'] = Label('')
        self['hwinfo'].setText('')
        if self.boxtype == 'et8000' or self.boxtype == 'et10000' or self.boxtype == 'et8500':
            self['faninfo'] = Label('')
            self['faninfo'].setText('')
        self['buttons'] = Label('')
        self['buttons'].setText('')
        self['buttons_red'] = Label('')
        self['buttons_yellow'] = Label('')
        self['buttons_blue'] = Label('')
        self['version'] = Label('')
        self.session.nav.stopService()
        self.closeFrontend()
        self.xmlFiles = {}
        self.readMainXml()
        self.location = self.locations[0]
        self.statusTimer = eTimer()
        self.statusTimer.callback.append(self.statusCallback)
        self.onLayoutFinish.append(self.postInitCallback)

    def postInitCallback(self):
        self['message_header'].setText('Message')
        self['message'].setText('')
        self['stbname'].setText(' %s - %s' % (self.boxtype.upper(), self.location.upper()))
        self['buttons_red'].setText('Location Of Test')
        self['buttons_yellow'].setText('Aging Test')
        self['version'].setText('Test Version: ' + JIG_VERSION)
        self.tuner_count = len(nimmanager.nim_slots)
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            if nimmanager.hasNimType("DVB-T2"):
                if nimmanager.hasNimType("DVB-C"):
                    self.tuners[0][0] = nimmanager.getNimType(0)
                    self.tuners[0][1] = nimmanager.getNimName(0).split()[0]
                if nimmanager.hasNimType("DVB-T2"):
                    self.tuners[1][0] = "DVB-T2"
                    self.tuners[1][1] = nimmanager.getNimName(0).split()[0]                  
            else:
                for x in range(len(self.tuners)):
                    if x < self.tuner_count:
                        self.tuners[x][0] = nimmanager.getNimType(x)
                        self.tuners[x][1] = nimmanager.getNimName(x).split()[0]
                    else:
                        idx = self.menu_tuner_index[0] + x
                        self['menuleft' + str(idx)].setBackgroundColorNum(2)
        elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S' or self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners[0][0] = nimmanager.getNimType(0)
                self.tuners[0][1] = nimmanager.getNimName(0).split()[0]
                if nimmanager.hasNimType("DVB-C"):
                    self.tuners[1][0] = nimmanager.getNimType(1)
                    self.tuners[1][1] = nimmanager.getNimName(1).split()[0]
                if nimmanager.hasNimType("DVB-T2"):
                    self.tuners[2][0] = "DVB-T2"
                    self.tuners[2][1] = nimmanager.getNimName(1).split()[0]
            else:
                for x in range(len(self.tuners)):
                    if x < self.tuner_count:
                        self.tuners[x][0] = nimmanager.getNimType(x)
                        self.tuners[x][1] = nimmanager.getNimName(x).split()[0]
                    else:
                        idx = self.menu_tuner_index[0] + x
                        self['menuleft' + str(idx)].setBackgroundColorNum(2)
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            if nimmanager.hasNimType("DVB-T2"):
                self.tuners[0][0] = nimmanager.getNimType(0)
                self.tuners[0][1] = nimmanager.getNimName(0).split()[0]
                if nimmanager.hasNimType("DVB-C"):
                    self.tuners[1][0] = nimmanager.nim_slots[1].getType()
                    self.tuners[1][1] = nimmanager.getNimName(1).split()[0]
                if nimmanager.hasNimType("DVB-T2"):
                    self.tuners[2][0] = nimmanager.nim_slots[1].getType()
                    self.tuners[2][1] = nimmanager.getNimName(1).split()[0]
                if nimmanager.hasNimType("DVB-T2"):
                    self.tuners[3][0] = "DVB-T2"
                    self.tuners[3][1] = nimmanager.getNimName(1).split()[0]
            else:
                for x in range(len(self.tuners)):
                    if x < self.tuner_count:
                        self.tuners[x][0] = nimmanager.getNimType(x)
                        self.tuners[x][1] = nimmanager.getNimName(x).split()[0]
                    else:
                        idx = self.menu_tuner_index[0] + x
                        self['menuleft' + str(idx)].setBackgroundColorNum(2)
        else:
            for x in range(len(self.tuners)):
                if x < self.tuner_count:
                    self.tuners[x][0] = nimmanager.getNimType(x)
                    self.tuners[x][1] = nimmanager.getNimName(x).split()[0]
                else:
                    idx = self.menu_tuner_index[0] + x
                    self['menuleft' + str(idx)].setBackgroundColorNum(2)
                    
        for x in range(self.total_left):
            if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
                if nimmanager.hasNimType("DVB-T2"):
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count+1:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
                else:
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
            elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
                if nimmanager.hasNimType("DVB-T2"):
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count+1:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
                else:
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
            elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                if nimmanager.hasNimType("DVB-T2"):
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count+1:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
                else:
                    if x in self.menu_tuner_index:
                        if x - self.menu_tuner_index[0] < self.tuner_count:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                        else:
                            self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])
            else:
                if x in self.menu_tuner_index:
                    if x - self.menu_tuner_index[0] < self.tuner_count:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' (' + self.tuners[x - self.menu_tuner_index[0]][0] + ') Test')
                    else:
                        self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x] + ' Test')
                else:
                    self['menuleft' + str(x)].setText(' ' + str(x + 1) + '. ' + self.menu_names[x])

        if self.has_security is True:
            self.setRightMenuSecurity(True)
        self.hideMessage()
        self.hideTunerInfo()
        self['buttons_blue'].hide()
        self.setScart()
        self.setMenuItem(0)
        if self.boxtype == 'et9x00':
            self.setTitle('88:88')
        self.loadServices()
        self.statusTimer.start(1000)

    def statusCallback(self):
        self.Console = Console()
        if self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == '7225S' or self.boxtype == 'hd61':
            if self.local_ip_eth0 == '0.0.0.0':
                self.Console.ePopen('ip addr show dev eth0', self.NetworkStatedataAvail, ['eth0', None])
            if self.has_eth1 is True:
                if self.local_ip_eth1 == '0.0.0.0':
                    self.Console.ePopen('ip addr show dev eth1', self.NetworkStatedataAvail, ['eth1', None])
        else:
            if self.local_ip_eth0 == '0.0.0.0':
                self.Console.ePopen('ip -o addr show dev eth0', self.NetworkStatedataAvail, ['eth0', None])
            if self.has_eth1 is True:
                if self.local_ip_eth1 == '0.0.0.0':
                    self.Console.ePopen('ip -o addr show dev eth1', self.NetworkStatedataAvail, ['eth1', None])
        if self.scislots > 0:
            if self.scislot[0] is False:
                self.runSmartcardTest(0)
            if self.scislots == 2:
                if self.scislot[1] is False:
                    self.runSmartcardTest(1)
        for x in range(self.usbslots):
            if self.usbslot[x] is False:
                self.runUsbTest(x)

        if self.cislots > 0:
            if self.cislot[0] is False:
                self.runCiTest(0)
            if self.cislots > 1:
                if self.cislot[1] is False:
                    self.runCiTest(1)
        self.runEsataTest()
        self.runSDcardTest()
        txt = ' MAC: ' + self.mac + '\n HW Version: ' + self.hardwareversion + '\n SW Version: ' + about.getEnigmaVersionString() + '\n IP ETH0: ' + self.local_ip_eth0
        if self.has_eth1 is True:
            txt += '\n IP ETH1: ' + self.local_ip_eth1
        self['hwinfo'].setText(txt)
        if self.boxtype == 'et8000' or self.boxtype == 'et10000' or self.boxtype == 'et8500':
            fd = open('/proc/stb/fp/fan')
            fan_state = fd.read().strip()
            fd.close()
            fd = open('/proc/stb/fp/temp_sensor')
            temperature = fd.read().strip()
            fd.close()
            txt = '  Fan Status: ' + fan_state
            txt += '\n  Temperature: ' + temperature + ' C'
            self['faninfo'].setText(txt)
        if self.type_test == self.TEST_TUNER:
            if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
                type = self.tuners[self.tuner_nr][0]
                if type == 'DVB-T' or type == 'DVB-T2':
                    txt = '\nvoltage state: 5V enable\n\n'
                    if type == 'DVB-S' or type == 'DVB-S2':
                        tuner_type = 'satellite'
                    elif type == 'DVB-C' or type == 'DVB-C2':
                        tuner_type = 'cable'
                    elif type == 'DVB-T' or type == 'DVB-T2':
                        tuner_type = 'terrestrial'
                    if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                        txt = txt + 'Press OK to stop'
                    else:
                        txt = txt + 'Press OK to next'
                    self['message'].setText(self.tune_text + txt)
                else:
                    self.frontend.getFrontendStatus(self.frontendStatus)
                    self.lockState.update()
                    if self.lockState.getValue(TunerInfo.LOCK) == 1:
                        txt = '\nLockstate: Locked\n\n'
                        if type == 'DVB-S' or type == 'DVB-S2':
                            tuner_type = 'satellite'
                        elif type == 'DVB-C' or type == 'DVB-C2':
                            tuner_type = 'cable'
                        elif type == 'DVB-T' or type == 'DVB-T2':
                            tuner_type = 'terrestrial'
                        if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                            txt = txt + 'Press OK to stop'
                        else:
                            txt = txt + 'Press OK to next'
                        self['message'].setText(self.tune_text + txt)
                        self.play_service()
            elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
                type = self.tuners[self.tuner_nr][0]
                if type == 'DVB-T' or type == 'DVB-T2':
                    txt = '\nvoltage state: 5V enable\n\n'
                    if type == 'DVB-S' or type == 'DVB-S2':
                        tuner_type = 'satellite'
                    elif type == 'DVB-C' or type == 'DVB-C2':
                        tuner_type = 'cable'
                    elif type == 'DVB-T' or type == 'DVB-T2':
                        tuner_type = 'terrestrial'
                    if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                        txt = txt + 'Press OK to stop'
                    else:
                        txt = txt + 'Press OK to next'
                    self['message'].setText(self.tune_text + txt)
                else:
                    self.frontend.getFrontendStatus(self.frontendStatus)
                    self.lockState.update()
                    if self.lockState.getValue(TunerInfo.LOCK) == 1:
                        txt = '\nLockstate: Locked\n\n'
                        if type == 'DVB-S' or type == 'DVB-S2':
                            tuner_type = 'satellite'
                        elif type == 'DVB-C' or type == 'DVB-C2':
                            tuner_type = 'cable'
                        elif type == 'DVB-T' or type == 'DVB-T2':
                            tuner_type = 'terrestrial'
                        if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                            txt = txt + 'Press OK to stop'
                        else:
                            txt = txt + 'Press OK to next'
                        self['message'].setText(self.tune_text + txt)
                        self.play_service()
            elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                type = self.tuners[self.tuner_nr][0]
                if type == 'DVB-T' or type == 'DVB-T2':
                    txt = '\nvoltage state: 5V enable\n\n'
                    if type == 'DVB-S' or type == 'DVB-S2':
                        tuner_type = 'satellite'
                    elif type == 'DVB-C' or type == 'DVB-C2':
                        tuner_type = 'cable'
                    elif type == 'DVB-T' or type == 'DVB-T2':
                        tuner_type = 'terrestrial'
                    if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                        txt = txt + 'Press OK to stop'
                    else:
                        txt = txt + 'Press OK to next'
                    self['message'].setText(self.tune_text + txt)
                else:
                    self.frontend.getFrontendStatus(self.frontendStatus)
                    self.lockState.update()
                    if self.lockState.getValue(TunerInfo.LOCK) == 1:
                        txt = '\nLockstate: Locked\n\n'
                        if type == 'DVB-S' or type == 'DVB-S2':
                            tuner_type = 'satellite'
                        elif type == 'DVB-C' or type == 'DVB-C2':
                            tuner_type = 'cable'
                        elif type == 'DVB-T' or type == 'DVB-T2':
                            tuner_type = 'terrestrial'
                        if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                            txt = txt + 'Press OK to stop'
                        else:
                            txt = txt + 'Press OK to next'
                        self['message'].setText(self.tune_text + txt)
                        self.play_service()
            elif self.frontend is not None:
                self.frontend.getFrontendStatus(self.frontendStatus)
                self.lockState.update()
                if self.lockState.getValue(TunerInfo.LOCK) == 1:
                    txt = '\nLockstate: Locked\n\n'
                    type = self.tuners[self.tuner_nr][0]
                    if type == 'DVB-S' or type == 'DVB-S2':
                        tuner_type = 'satellite'
                    elif type == 'DVB-C' or type == 'DVB-C2':
                        tuner_type = 'cable'
                    elif type == 'DVB-T' or type == 'DVB-T2':
                        tuner_type = 'terrestrial'
                    if self.tune_index + 1 == self.getCount(tuner_type, self.location.lower()):
                        txt = txt + 'Press OK to stop'
                    else:
                        txt = txt + 'Press OK to next'
                    self['message'].setText(self.tune_text + txt)
                    self.play_service()
        if self.type_test == self.TEST_HDD:
            if self.frontend is not None:
                self.frontend.getFrontendStatus(self.frontendStatus)
                self.lockState.update()
                if self.lockState.getValue(TunerInfo.LOCK) == 1:
                    self.record_service()

    def evTunedInEvent(self):
        self.zapped = True

    def evTuneFailedEvent(self):
        self.zapped = False
        service = self.session.nav.getCurrentService()
        info = service and service.info()
        error = info and info.getInfo(iServiceInformation.sDVBState)
        error = {eDVBServicePMTHandler.eventNoResources: _('No free tuner!'),
         eDVBServicePMTHandler.eventTuneFailed: _('Tune failed!'),
         eDVBServicePMTHandler.eventNoPAT: _('No data on transponder!\t(Timeout reading PAT)'),
         eDVBServicePMTHandler.eventNoPATEntry: _('Service not found!\t(SID not found in PAT)'),
         eDVBServicePMTHandler.eventNoPMT: _('Service invalid!\t(Timeout reading PMT)'),
         eDVBServicePMTHandler.eventMisconfiguration: _('Service unavailable!\tCheck tuner configuration!')}.get(error)
        if service:
            self.session.nav.stopService()
            self.closeFrontend()
        type = self.tuners[self.tuner_nr][0]
        if type == 'DVB-S' or type == 'DVB-S2':
            self.tuneSatellite(1)
        elif type == 'DVB-C' or type == 'DVB-C2':
            self.tuneCable(1)
        elif type == 'DVB-T' or type == 'DVB-T2':
            self.tuneTerrestrial(1)

    def evEndEvent(self):
        self.zapped = False
        if self.type_test == self.TEST_HDD:
            self.record_start = False

    def evEOFEvent(self):
        self.zapped = False
        if self.type_test == self.TEST_HDD:
            self.record_start = False
        elif self.type_test == self.TEST_AGING:
            service = self.session.nav.getCurrentlyPlayingServiceReference()
            if service:
                self.session.nav.stopService()
                self.session.nav.playService(service)

    def loadServices(self):
        os.system('cp /usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/lamedb /etc/enigma2/lamedb')
        os.system('cp /usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/userbouquet.LastScanned.tv /etc/enigma2/userbouquet.LastScanned.tv')
        os.system('cp /usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/bouquets.tv /etc/enigma2/bouquets.tv')
        eDVBDB.getInstance().reloadBouquets()
        eDVBDB.getInstance().reloadServicelist()

    def deleteServices(self):
        pass

    def play_service(self):
        service = '-1:0:0:0:0:0:0:0:0:0'
        type = self.tuners[self.tuner_nr][0]
        cnt = 0
        found = False
        if type == 'DVB-S' or type == 'DVB-S2':
            for x in self.xmlFiles['satellite']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[14]
        elif type == 'DVB-C' or type == 'DVB-C2':
            for x in self.xmlFiles['cable']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[8]
        elif type == 'DVB-T' or type == 'DVB-T2':
            for x in self.xmlFiles['terrestrial']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[13]
        if self.tune_test_start is True and self.zapped is False:
            self.closeFrontend()
            self.session.nav.playService(eServiceReference(service))

    def record_service(self):
        service = '-1:0:0:0:0:0:0:0:0:0'
        type = self.tuners[self.tuner_nr][0]
        cnt = 0
        found = False
        if type == 'DVB-S' or type == 'DVB-S2':
            for x in self.xmlFiles['satellite']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[14]
        elif type == 'DVB-C' or type == 'DVB-C2':
            for x in self.xmlFiles['cable']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[8]
        elif type == 'DVB-T' or type == 'DVB-T2':
            for x in self.xmlFiles['terrestrial']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                service = x[13]
        if self.tune_test_start is True and self.zapped is False and self.record_test_start is True and self.record_start is False and self.record_end is False and self.record_play_start is False:
            if self.zapped:
                self.session.nav.stopService()
            self.closeFrontend()
            self.session.nav.playService(eServiceReference(service))
            if self.record_test_start is True and self.record_start is False:
                self.record = self.session.nav.recordService(eServiceReference(service))
                if self.record is not None:
                    self.record.prepare(self.recordTestFileName, -1, -1, -1, '', '', '', False, False)
                    self.record.start()
                    self.count = 0
                    self.record_start = True
                    self.showMessage()
                    self['message'].setText('HDD Test running\n\nRecording...\n\nPress OK to stop')
        elif self.tune_test_start is True and self.zapped is True and self.record_test_start is True and self.record_start is True and self.record_end is False and self.record_play_start is False:
            if self.count > self.record_time:
                if self.record is not None:
                    self.record.stop()
                    self.session.nav.stopRecordService(self.record)
                    del self.record
                    self.record = None
                    self.zapped = False
                    self.record_start = False
                    self.record_end = True
                    self.session.nav.stopService()
                    service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
                    self.session.nav.playService(service)
                    self.showMessage()
                    self['message'].setText('HDD Test running\n\nRecording finished...\n\nPress OK to play the file\nDirection Key(UP/DOWN) to stop')
                    self.count = 0
            else:
                msg = 'HDD Test running\n\nRecording... (' + str(5 - self.count) + ')\n\nPress OK to stop'
                self['message'].setText(msg)
                self.count = self.count + 1

    def NetworkStatedataAvail(self, data, retval, extra_args):
        self.list = []
        if 'eth0' in data:
            eth0 = True
        else:
            eth0 = False
        for line in data.splitlines():
            if 'link/ether' in line:
                self.mac = line.split('link/ether')[1].split(' ')[1]
            else:
                tmp2 = line.split('inet ')
                if len(tmp2) > 1:
                    tmp3 = tmp2[1].split('/')
                    if eth0 is True:
                        self.local_ip_eth0 = tmp3[0]
                        if self.local_ip_eth0 != '':
                            self.setRightMenuEthernet(0, True)
                    else:
                        self.local_ip_eth1 = tmp3[0]
                        if self.local_ip_eth1 != '':
                            self.setRightMenuEthernet(1, True)

    def runSmartcardTest(self, slot):
        if self.boxtype == 'et10000' or self.boxtype == 'et8000':
            self.fd = self.dll.opensci('/dev/sci%d' % slot)
            status = self.dll.getscistatus(self.fd)
            if status == 1:
                atr = ''
                ret = 0
                data = ''
                ret = self.dll.atrstart(self.fd)
                if ret > 1:
                    for x in range(4):
                        atr += '%02x ' % self.dll.getatrbuffer(x)
                        if '3b' in atr or '3f' in atr:
                            self.scislot[slot] = True
                            self.setRightMenuSmartcard(slot, True)

            self.dll.closesci(self.fd)
        elif self.boxtype == 'et9x00' or self.boxtype == 'et7000' or self.boxtype == 'et7500' or self.boxtype == 'et8500' or self.boxtype == 'g300':
            p = os.popen('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/sctest /dev/sci%d' % slot)
            ret = p.read()
            if ret.strip() == '1':
                self.scislot[slot] = True
                self.setRightMenuSmartcard(slot, True)
            p.close()
    	elif self.boxtype == '7000S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7210S' or self.boxtype == '7220S':
            p = os.popen('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/sctest /dev/sci%d' % slot)
            ret = p.read()
            if ret.strip() == '1':
                self.scislot[slot] = True
                self.setRightMenuSmartcard(slot, True)
            p.close()
    	elif self.boxtype == '7005S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7215S' or self.boxtype == '7225S':
            p = os.popen('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/sctest /dev/sci%d' % slot)
            ret = p.read()
            if ret.strip() == '1':
                self.scislot[slot] = True
                self.setRightMenuSmartcard(slot, True)
            p.close()
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            self.smartcard = self.readFile('/proc/smartcard')
            if self.smartcard == '1':
                self.scislot[slot] = True
                self.setRightMenuSmartcard(slot, True)
            
    def runUsbTest(self, slot):
        ret = self.readlog(slot)
        if ret != '':
            for x in ret:
                if 'new' in x and 'USB device' in x:
                    if self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                        if self.usbslot_target[slot] in x.split(':')[3].split('usb ')[1]:
                            self.usbslot_target_found[slot] = True
                        if self.usbslot_target2[slot] in x.split(':')[3].split('usb ')[1]:
                            self.usbslot_target_found[slot] = True
                    else:
                        if self.usbslot_target[slot] in x.split(':')[3].split(' ')[2]:
                            self.usbslot_target_found[slot] = True
                        if self.usbslot_target[slot] in x.split(']')[1].split(' ')[2].split(':')[0]:
                            self.usbslot_target_found[slot] = True
                if 'Attached' in x and self.usbslot_target_found[slot] is True:
                    self.usbslot[slot] = True
                    self.setRightMenuUsb(slot, True)
                    break

    def runCiTest(self, slot):
        if len(eDVBCIInterfaces.getInstance().readCICaIds(slot)) > 0:
            self.cislot[slot] = True
            self.setRightMenuCi(slot, True)

    def runEsataTest(self):
        ret = self.readEsatalog()
        if ret != '':
            for x in ret:
                if self.has_esata is True:
                    if self.boxtype == 'g300':
                        if 'ata2: SATA link up' in x:
                            self.setRightMenuEsata(True)
                            break
                        if 'ata2: SATA link down' in x:
                            self.setRightMenuEsata(False)
                            break
                    else:
                        if 'SATA link up' in x:
                            self.setRightMenuEsata(True)
                            break
                        if 'SATA link down' in x:
                            self.setRightMenuEsata(False)
                            break
                if self.has_sata is True:
                    if self.boxtype == 'g300':
                        if 'ata1: SATA link up' in x:
                            self.setRightMenusata(True)
                            break
                        if 'ata1: SATA link down' in x:
                            self.setRightMenusata(False)
                            break
                    else:
                        if 'SATA link up' in x:
                            self.setRightMenusata(True)
                            break
                        if 'SATA link down' in x:
                            self.setRightMenusata(False)
                            break

    def runSDcardTest(self):
        ret = self.readSDcardlog()
        if ret != '':
            for x in ret:
                if 'card connected!' in x:
                    self.setRightMenuSDcard(True)
                    break
                if 'card disconnected!' in x:
                    self.setRightMenuSDcard(False)
                    break

    def runAgingTest(self, val):
        if val == 1:
            found = False
            dirname = '/media'
            for f in os.listdir(dirname):
                path = os.path.join(dirname, f)
                if os.path.isdir(path):
                    fullpath = path + '/luxtv.ts'
                    if os.path.exists(fullpath):
                        service = eServiceReference(1, 0, fullpath)
                        self.session.nav.playService(service)
                        found = True
                        self['message'].setText('AGING Test running\n\nPress OK to stop')
                        break

            if found is False:
                self['message'].setText('AGING Test failed\n\nCould not find content file on usb disk!!!\n\nPress OK to stop')
            self.showMessage()
            self.want_ok = True
            self.type_test = self.TEST_AGING
        else:
            self.hideMessage()
            self.session.nav.stopService()
            self.type_test = self.TEST_NONE
            self.want_ok = False
            service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
            self.session.nav.playService(service)
            if self.runAgingTestKeyActionProtect is False:
                self.keyDown()
            else:
                self.runAgingTestKeyActionProtect = False

    def runHdmiTest(self, val):
        if val == 1:
            self.session.nav.stopService()
            self.dll.set_hdmi_in(1)
            self.showMessage()
            self['message'].setText('HDMI Test running\n\nPress OK to stop')
            self.want_ok = True
            self.type_test = self.TEST_HDMI_IN
        else:
            self.dll.set_hdmi_in(0)
            self.hideMessage()
            self.type_test = self.TEST_NONE
            self.want_ok = False
            service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
            self.session.nav.playService(service)
            self.keyDown()

    def runKeyTest(self, val):
        if val == 1:
            self.showMessage()
            self['message'].setText('KEY Test running\n\nPress OK to stop')
            self.TEST_KEYS = True
            self.type_test = self.TEST_KEYS
        else:
            self.hideMessage()
            self.type_test = self.TEST_NONE
            self.TEST_KEYS = False
            self.keyDown()

    def runScartTest(self, val):
        if val == 1:
            txt = ''
            self.type_test = self.TEST_SCART
            if self.scart_type == 0:
                if self.scart_aspect_ratio == 0:
                    config.av.aspect.value = "4:3"
                    scart_aspect_ratio = '4:3'
                    txt = 'Scart CVBS(' + scart_aspect_ratio + ') running\n\nPress OK to next'
                    found = False
                    dirname = '/media'
                    for f in os.listdir(dirname):
                        path = os.path.join(dirname, f)
                        if os.path.isdir(path):
                            fullpath = path + '/color_bar.mpg'
                            if os.path.exists(fullpath):
                                found = True
                                reference = eServiceReference(4097, 0, fullpath)
                                self.session.nav.playService(reference)
                                break

                    if found is False:
                        txt = 'Can not found the Test Content\n\nPress OK to stop'
                        self.scart_aspect_ratio = 0
                        self.want_ok = True
                        self.scart_type = 0
                    f = open('/etc/videomode', 'w')
                    f.write('pal')
                    f.close()
##                    f = open('/proc/stb/video/videomode_50hz', 'w')
##                    f.write('pal')
##                    f.close()
##                    f = open('/proc/stb/video/videomode_60hz', 'w')
##                    f.write('pal')
##                    f.close()
                    self.setScart(self.scart_type, self.scart_aspect_ratio)
                    self.scart_aspect_ratio = 1
                elif self.scart_aspect_ratio == 1:
                    scart_aspect_ratio = '16:9'
                    txt = 'Scart CVBS(' + scart_aspect_ratio + ') running\n\nPress OK to next'
                    self.setScart(self.scart_type, self.scart_aspect_ratio)
                    self.scart_type = 1
                    self.scart_aspect_ratio = 0
                self.showMessage()
                self['message'].setText(txt)
            elif self.scart_type == 1:
                if self.scart_aspect_ratio == 0:
                    scart_aspect_ratio = '4:3'
                    txt = 'Scart RGB(' + scart_aspect_ratio + ') running\n\nPress OK to next'
                    self.setScart(self.scart_type, self.scart_aspect_ratio)
                    self.scart_aspect_ratio = 1
                elif self.scart_aspect_ratio == 1:
                    scart_aspect_ratio = '16:9'
                    txt = 'Scart RGB(' + scart_aspect_ratio + ') running\n\nPress OK to stop'
                    self.want_ok = True
                    self.setScart(self.scart_type, self.scart_aspect_ratio)
                    self.scart_aspect_ratio = 0
                    self.scart_type = 0
                self.showMessage()
                self['message'].setText(txt)
        else:
            self.session.nav.stopService()
            self.hideMessage()
            self.scart_aspect_ratio = 0
            self.scart_type = 0
            self.type_test = self.TEST_NONE
            self.setScart()
            self.want_ok = False
            f = open('/etc/videomode', 'w')
            f.write('720p50')
            f.close()
##            f = open('/proc/stb/video/videomode_50hz', 'w')
##            f.write('720p50')
##            f.close()
##            f = open('/proc/stb/video/videomode_60hz', 'w')
##            f.write('720p50')
##            f.close()
            service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
            self.session.nav.playService(service)
            if self.runAgingTestKeyActionProtect is False:
                self.keyDown()
            else:
                self.runAgingTestKeyActionProtect = False

    def runHDDTest(self, val):
        if val == 1:
            self.type_test = self.TEST_HDD
            self.want_ok = True
            self.tune_index = 0
            self.tuner_nr = 0
            self.session.nav.stopService()
            self.closeFrontend()
            if os.path.exists('/media/hdd') and os.path.isdir('/media/hdd'):
                self.isExistHDD = True
            else:
                self.isExistHDD = False
                self.showMessage()
                self['message'].setText('HDD Test running\n\nNo HDD...\n\nPress OK to stop')
                return
            self.showMessage()
            self['message'].setText('HDD Test running\n\nService Tunning...\n\nPress OK to stop')
            type = self.tuners[self.tuner_nr][0]
            if type == 'Unknown':
                self.keyDown()
                return
            InitNimManager(nimmanager)
            cnt = 0
            found = False
            if type == 'DVB-S' or type == 'DVB-S2':
                for x in self.xmlFiles['satellite']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.record_test_start = True
                    band = x[12]
                    satpos = x[7]
                    khz = x[13]
                    self.createSatelliteConfig(self.tuner_nr, band, satpos, khz)
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneSatellite()
            elif type == 'DVB-C' or type == 'DVB-C2':
                for x in self.xmlFiles['cable']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.record_test_start = True
                    self.createCableConfig()
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneCable()
            elif type == 'DVB-T' or type == 'DVB-T2':
                for x in self.xmlFiles['terrestrial']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.record_test_start = True
                    self.createTerrestrialConfig()
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneTerrestrial()
        elif val == 2:
            self.record_play_start = True
            if not fileExists(self.recordTestFileName):
                self.isExistHDD = False
                self.showMessage()
                self['message'].setText('HDD Test running\n\nNo HDD...\n\nPress OK to stop')
                return
            reference = eServiceReference(1, 0, self.recordTestFileName)
            self.session.nav.playService(reference)
            self.showMessage()
            self['message'].setText('HDD Test running\n\nPlaying the recorded file...\n\nPress OK to stop')
        else:
            if self.record is not None:
                self.record.stop()
                self.session.nav.stopRecordService(self.record)
                del self.record
                self.record = None
            self.session.nav.stopService()
            self.closeFrontend(True)
            self.hideMessage()
            self.want_ok = False
            self.type_test = self.TEST_NONE
            self.tune_test_start = False
            self.zapped = False
            self.record_test_start = False
            self.record_start = False
            self.record_end = False
            self.record_play_start = False
            self.isExistHDD = False
            os.system('rm -fR /media/hdd/record_test.*')
            service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
            self.session.nav.playService(service)
            if self.runAgingTestKeyActionProtect is False:
                self.keyDown()
            else:
                self.runAgingTestKeyActionProtect = False

    def runRemovePlugin(self):
        self.showMessage()
        self['message'].setText('REMOVE PLUGIN\n\nPress BLUE BUTTON (       ) to confirm,\n      EXIT to abort                            ')
        self.type_test = self.TEST_REMOVE
        self.want_ok = True
        self['buttons_blue'].show()

    def runNextTunerTest(self):
        self.session.nav.stopService()
        self.closeFrontend()
        InitNimManager(nimmanager)
        cnt = 0
        found = False
        type = self.tuners[self.tuner_nr][0]
        if type == 'DVB-S' or type == 'DVB-S2':
            if self.tune_index == self.getCount('satellite', self.location.lower()):
                self.tune_index = 0
                self.keyDown()
                return
            for x in self.xmlFiles['satellite']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                band = x[12]
                satpos = x[7]
                khz = x[13]
                self.createSatelliteConfig(self.tuner_nr, band, satpos, khz)
                nimmanager.sec.update()
                self.openFrontend()
                self.tuneSatellite()
        elif type == 'DVB-C' or type == 'DVB-C2':
            if self.tune_index == self.getCount('cable', self.location.lower()):
                self.tune_index = 0
                self.keyDown()
                return
            for x in self.xmlFiles['cable']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                self.createCableConfig()
                nimmanager.sec.update()
                self.openFrontend()
                self.tuneCable()
        elif type == 'DVB-T' or type == 'DVB-T2':
            if self.tune_index == self.getCount('terrestrial', self.location.lower()):
                self.tune_index = 0
                self.keyDown()
                return
            for x in self.xmlFiles['terrestrial']:
                if x[0] == self.location.lower():
                    if cnt == self.tune_index:
                        found = True
                        break
                    cnt += 1

            if found:
                self.createTerrestrialConfig()
                nimmanager.sec.update()
                self.openFrontend()
                self.tuneTerrestrial()

    def runTunerTest(self, val):
        self.session.nav.stopService()
        self.closeFrontend()
        if val == 1:
            self.tuner_nr = self.leftmenu_idx - self.menu_tuner_index[0]
            type = self.tuners[self.tuner_nr][0]
            if type == 'Unknown':
                self.keyDown()
                return
            InitNimManager(nimmanager)
            self.want_ok = True
            self.tune_index = 0
            cnt = 0
            found = False
            if type == 'DVB-S' or type == 'DVB-S2':
                for x in self.xmlFiles['satellite']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.type_test = self.TEST_TUNER
                    band = x[12]
                    satpos = x[7]
                    khz = x[13]
                    self.createSatelliteConfig(self.tuner_nr, band, satpos, khz)
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneSatellite()
            elif type == 'DVB-C' or type == 'DVB-C2':
                for x in self.xmlFiles['cable']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.type_test = self.TEST_TUNER
                    self.createCableConfig()
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneCable()
            elif type == 'DVB-T' or type == 'DVB-T2':
                for x in self.xmlFiles['terrestrial']:
                    if x[0] == self.location.lower():
                        if cnt == self.tune_index:
                            found = True
                            break
                        cnt += 1

                if found:
                    self.tune_test_start = True
                    self.type_test = self.TEST_TUNER
                    self.createTerrestrialConfig()
                    nimmanager.sec.update()
                    self.openFrontend()
                    self.tuneTerrestrial()

        else:
            self.hideMessage()
            self.want_ok = False
            self.type_test = self.TEST_NONE
            self.tune_test_start = False
            self.zapped = False
            self.session.nav.stopService()
            self.closeFrontend(True)
            service = eServiceReference(4097, 0, '/usr/share/bootlogo.mvi')
            self.session.nav.playService(service)

    def vfd_write(self, text):
        open("/dev/dbox/oled0", "w").write(text)

    def runFrontLEDTest(self, val):
        if val == 1:
            if fileExists("/proc/stb/lcd/powerled"):
                f = open("/proc/stb/lcd/powerled", "w")
                f.write("1")
                f.close()
            if self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S':
                if fileExists("/proc/stb/lcd/oled_brightness"):
                    f = open("/proc/stb/lcd/oled_brightness", "w")
                    f.write("255")
                    f.close()
                if fileExists("/dev/dbox/oled0"):
                    self.clock = "88:88"
                    self.vfd_write(self.clock)
            elif self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7225S':
                if fileExists("/proc/stb/lcd/oled_brightness"):
                    f = open("/proc/stb/lcd/oled_brightness", "w")
                    f.write("255")
                    f.close()
                if fileExists("/dev/dbox/oled0"):
                    self.clock = "88:88"
                    self.vfd_write(self.clock)
            elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                if fileExists("/proc/stb/lcd/oled_brightness"):
                    f = open("/proc/stb/lcd/oled_brightness", "w")
                    f.write("255")
                    f.close()
                if fileExists("/dev/dbox/oled0"):
                    self.clock = "88:88"
                    self.vfd_write(self.clock)
            self.showMessage()
            self['message'].setText('Front Display Test running\n\nWhile testing, the screen is off\nAfter screen off, press OK or Directrion key (UP/DOWN) to test stop, then the screen is on\n\nPress OK to continue test\nPress Direction Key(UP/DOWN) to stop')
            self.type_test = self.TEST_FRONT_LED
            self.want_ok = True
            if self.ledtest:
                eAVSwitch.getInstance().setInput(2)
                self.setTitle('Press OK Key')
                self.ledtest = False
            else:
                self.ledtest = True
        else:
#            if fileExists("/proc/stb/lcd/powerled"):
#                f = open("/proc/stb/lcd/powerled", "w")
#                f.write("0")
#                f.close()
#            if self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S':
#                if fileExists("/proc/stb/lcd/oled_brightness"):
#                    f = open("/proc/stb/lcd/oled_brightness", "w")
#                    f.write("0")
#                    f.close()
            self.hideMessage()
            self.want_ok = False
            self.type_test = self.TEST_NONE
            eAVSwitch.getInstance().setInput(0)
            self.setTitle('Factoty Test')
            self.ledtest = False
            if self.runAgingTestKeyActionProtect is False:
                self.keyDown()
            else:
                self.runAgingTestKeyActionProtect = False

    def setScart(self, colorformat = -1, aspect = -1):
        if colorformat == 0:
            format = 'cvbs'
        elif colorformat == 1:
            format = 'rgb'
        else:
            format = 'yuv'
        f = open('/proc/stb/avs/0/colorformat', 'w')
        f.write(format)
        f.close()
        if aspect == 0:
            aspectratio = '4:3'
        elif aspect == 1:
            aspectratio = '16:9'
        else:
            aspectratio = 'any'
        f = open('/proc/stb/video/aspect', 'w')
        f.write(aspectratio)
        f.close()

    def setKuBandLnb(self, idx, satpos, khz):
        nim = nimmanager.nim_slots[idx]
        nimConfig = nim.config.dvbs
        nimConfig.configMode.value = 'simple'
        nimConfig.diseqcMode.value = 'single'
        nimConfig.diseqcA.value = satpos

    def setCbandLnb(self, idx, satpos, khz):
        nim = config.Nims[idx].dvbs
        nim.configMode.value = 'advanced'
        nim.advanced = ConfigSubsection()
        nim.advanced.sat = ConfigSubDict()
        nim.advanced.sats = ConfigSatlist(nimmanager.satList, satpos)
        nim.advanced.lnb = ConfigSubDict()
        nim.advanced.lnb[0] = ConfigNothing()
        for x in nimmanager.satList:
            tmp = ConfigSubsection()
            tmp.voltage = ConfigSelection(advanced_voltage_choices, 'polarization')
            tmp.tonemode = ConfigSelection(advanced_tonemode_choices, 'band')
            tmp.usals = ConfigYesNo(True)
            tmp.rotorposition = ConfigInteger(default=1, limits=(1, 255))
            if x[0] == int(satpos):
                lnb = ConfigSelection(advanced_lnb_choices, '1')
                if int(khz) == 1:
                    tmp.tonemode = ConfigSelection(advanced_tonemode_choices, 'on')
            else:
                lnb = ConfigSelection(advanced_lnb_choices, '0')
            lnb.slot_id = 0
            tmp.lnb = lnb
            nim.advanced.sat[x[0]] = tmp

        for x in range(3601, 4100):
            tmp = ConfigSubsection()
            tmp.voltage = ConfigSelection(advanced_voltage_choices, 'polarization')
            tmp.tonemode = ConfigSelection(advanced_tonemode_choices, 'band')
            tmp.usals = ConfigYesNo(default=True)
            tmp.rotorposition = ConfigInteger(default=1, limits=(1, 255))
            lnbnum = 33 + x - 3601
            lnb = ConfigSelection([('0', 'not available'), (str(lnbnum), 'LNB %d' % lnbnum)], '0')
            lnb.slot_id = 0
            tmp.lnb = lnb
            nim.advanced.sat[x] = tmp

        section = nim.advanced.lnb[1] = ConfigSubsection()
        section.lofl = ConfigInteger(default=9750, limits=(0, 99999))
        section.lofh = ConfigInteger(default=10600, limits=(0, 99999))
        section.threshold = ConfigInteger(default=11700, limits=(0, 99999))
        section.increased_voltage = ConfigYesNo(False)
        section.toneburst = ConfigSelection(advanced_lnb_toneburst_choices, 'none')
        section.longitude = ConfigNothing()
        section.commitedDiseqcCommand = ConfigSelection(advanced_lnb_csw_choices, 'none')
        if int(khz) == 1:
            tmp = ConfigSelection(advanced_lnb_diseqcmode_choices, '1_0')
            if self.location.lower() == 'korea':
                if int(satpos) == 1056:
                    section.commitedDiseqcCommand = ConfigSelection(advanced_lnb_csw_choices, 'AA')
                else:
                    section.commitedDiseqcCommand = ConfigSelection(advanced_lnb_csw_choices, 'AB')
        else:
            tmp = ConfigSelection(advanced_lnb_diseqcmode_choices, 'none')
        tmp.section = section
        section.diseqcMode = tmp
        section.fastDiseqc = ConfigYesNo(False)
        section.sequenceRepeat = ConfigYesNo(False)
        section.commandOrder1_0 = ConfigSelection(advanced_lnb_commandOrder1_0_choices, 'ct')
        section.commandOrder = ConfigSelection(advanced_lnb_commandOrder_choices, 'ct')
        section.uncommittedDiseqcCommand = ConfigSelection(advanced_lnb_ucsw_choices)
        section.diseqcRepeats = ConfigSelection(advanced_lnb_diseqc_repeat_choices, 'none')
        section.prio = ConfigSelection(prio_list, '-1')
        section.unicable = ConfigNothing()
        tmp = ConfigSelection(lnb_choices, 'c_band')
        tmp.slot_id = 0
        section.lof = tmp

    def createSatelliteConfig(self, idx, band, satpos, khz):
        if band == 'ku':
            self.setKuBandLnb(idx, satpos, khz)
        else:
            self.setCbandLnb(idx, satpos, khz)

    def createCableConfig(self):
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            eDVBResourceManager.getInstance().setFrontendType(nimmanager.nim_slots[self.tuner_nr].frontend_id, 'DVB-C')
            nimmanager.nim_slots[self.tuner_nr].type = 'DVB-C'
            idx = 0
            typeList = []
            for id in nimmanager.nim_slots[self.tuner_nr].getMultiTypeList().keys():
                type = nimmanager.nim_slots[self.tuner_nr].getMultiTypeList()[id]
                if type == 'DVB-T2' or type == 'DVB-T':
                    idx = id
                typeList.append((id, type))
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            eDVBResourceManager.getInstance().setFrontendType(nimmanager.nim_slots[self.tuner_nr].frontend_id, 'DVB-C')
            nimmanager.nim_slots[self.tuner_nr].type = 'DVB-C'
            idx = 0
            typeList = []
            for id in nimmanager.nim_slots[self.tuner_nr].getMultiTypeList().keys():
                type = nimmanager.nim_slots[self.tuner_nr].getMultiTypeList()[id]
                if type == 'DVB-T2' or type == 'DVB-T':
                    idx = id
                typeList.append((id, type))
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            eDVBResourceManager.getInstance().setFrontendType(nimmanager.nim_slots[self.tuner_nr].frontend_id, 'DVB-C')
            nimmanager.nim_slots[self.tuner_nr].type = 'DVB-C'
            idx = 0
            typeList = []
            for id in nimmanager.nim_slots[self.tuner_nr].getMultiTypeList().keys():
                type = nimmanager.nim_slots[self.tuner_nr].getMultiTypeList()[id]
                if type == 'DVB-T2' or type == 'DVB-T':
                    idx = id
                typeList.append((id, type))

        nim = config.Nims[self.tuner_nr].dvbc
        nim.configMode = ConfigSelection(choices={'enabled': _('enabled'),
         'nothing': _('nothing connected')}, default='enabled')
        nim.cable = ConfigSubsection()
        nim.cable.scan_networkid = ConfigInteger(default=0, limits=(0, 9999))
        possible_scan_types = [('bands', _('Frequency bands')), ('steps', _('Frequency steps'))]
        possible_scan_types.append(('provider', _('Provider')))
        nim.cable.scan_provider = ConfigSelection(default='0', choices=list)
        nim.cable.scan_type = ConfigSelection(default='bands', choices=possible_scan_types)
        nim.cable.scan_band_EU_VHF_I = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_MID = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_VHF_III = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_UHF_IV = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_UHF_V = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_SUPER = ConfigYesNo(default=True)
        nim.cable.scan_band_EU_HYPER = ConfigYesNo(default=True)
        nim.cable.scan_band_US_LOW = ConfigYesNo(default=False)
        nim.cable.scan_band_US_MID = ConfigYesNo(default=False)
        nim.cable.scan_band_US_HIGH = ConfigYesNo(default=False)
        nim.cable.scan_band_US_SUPER = ConfigYesNo(default=False)
        nim.cable.scan_band_US_HYPER = ConfigYesNo(default=False)
        nim.cable.scan_frequency_steps = ConfigInteger(default=1000, limits=(1000, 10000))
        nim.cable.scan_mod_qam16 = ConfigYesNo(default=False)
        nim.cable.scan_mod_qam32 = ConfigYesNo(default=False)
        nim.cable.scan_mod_qam64 = ConfigYesNo(default=True)
        nim.cable.scan_mod_qam128 = ConfigYesNo(default=False)
        nim.cable.scan_mod_qam256 = ConfigYesNo(default=True)
        nim.cable.scan_sr_6900 = ConfigYesNo(default=True)
        nim.cable.scan_sr_6875 = ConfigYesNo(default=True)
        nim.cable.scan_sr_ext1 = ConfigInteger(default=0, limits=(0, 7230))
        nim.cable.scan_sr_ext2 = ConfigInteger(default=0, limits=(0, 7230))

    def createTerrestrialConfig(self):
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S':
            self.tuner_nr  = 0
        elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            self.tuner_nr  = 1
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            self.tuner_nr  = 0
        elif self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            self.tuner_nr  = 1
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            self.tuner_nr  = 1
        eDVBResourceManager.getInstance().setFrontendType(nimmanager.nim_slots[self.tuner_nr].frontend_id, 'DVB-T2')
        nimmanager.nim_slots[self.tuner_nr].type = 'DVB-T2'
        idx = 0
        typeList = []
        for id in nimmanager.nim_slots[self.tuner_nr].getMultiTypeList().keys():
            type = nimmanager.nim_slots[self.tuner_nr].getMultiTypeList()[id]
            if type == 'DVB-T2' or type == 'DVB-T':
                idx = id
            typeList.append((id, type))

        nim = config.Nims[self.tuner_nr]
        nim.multiType = ConfigSelection(typeList, str(idx))
        nim.multiType.fe_id = self.tuner_nr
        nim.dvbt.configMode = ConfigSelection(choices={'enabled': _('enabled'),
         'nothing': _('nothing connected')}, default='enabled')
        list = []
        n = 0
        for x in nimmanager.terrestrialsList:
            list.append((str(n), x[1]))
            n += 1

        nim.dvbt.terrestrial = ConfigSelection(choices=list, default='Europe, Middle East, Africa: DVB-T Frequencies')
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            nim.dvbt.terrestrial_5V = ConfigOnOff(True)
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            nim.dvbt.terrestrial_5V = ConfigOnOff(True)
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            nim.dvbt.terrestrial_5V = ConfigOnOff(True)
        else:
            nim.dvbt.terrestrial_5V = ConfigOnOff(default=False)
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S':
            self.tuner_nr  = 1
        elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            self.tuner_nr  = 2
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            self.tuner_nr  = 1
        elif self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            self.tuner_nr  = 2
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            self.tuner_nr  = 3

    def openFrontend(self):
        print '>>>>>>>>>>>>> OPEN FRONTEND, %d <<<<<<<<<<<<<<<<<<' % self.tuner_nr
        res_mgr = eDVBResourceManager.getInstance()
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S':
            type = self.tuners[self.tuner_nr][0]
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 0
        elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            type = self.tuners[self.tuner_nr][0]
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 1
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            type = self.tuners[self.tuner_nr][0]
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 0
        elif self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            type = self.tuners[self.tuner_nr][0]
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 1
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            type = self.tuners[self.tuner_nr][0]
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 1
        if res_mgr:
            self.raw_channel = res_mgr.allocateRawChannel(self.tuner_nr)
            if self.raw_channel:
                self.frontend = self.raw_channel.getFrontend()
                if self.frontend:
                    if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S':
                        if type == 'DVB-T2' or type == 'DVB-T':
                            self.tuner_nr  = 1
                    elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
                        if type == 'DVB-T2' or type == 'DVB-T':
                            self.tuner_nr  = 2
                    elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
                        if type == 'DVB-T2' or type == 'DVB-T':
                            self.tuner_nr  = 1
                    elif self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
                        if type == 'DVB-T2' or type == 'DVB-T':
                            self.tuner_nr  = 2
                    elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                        if type == 'DVB-T2' or type == 'DVB-T':
                            self.tuner_nr  = 3
                    return True
                print '!!!!!!!!!!!!! FAILED TO GET FRONTEND, %d  !!!!!!!!!!!!!!!!!!' % self.tuner_nr
            else:
                print '!!!!!!!!!!!!! FAILED TO ALLOCATE RAW CHANNEL, %d  !!!!!!!!!!!!!!!!!!' % self.tuner_nr
        else:
            print '!!!!!!!!!!!!! FAILED TO GET RESOURCE MANAGER INSTANCE, %d  !!!!!!!!!!!!!!!!!!' % self.tuner_nr
        if self.boxtype == '7000S' or self.boxtype == '7300S' or self.boxtype == '7400S':
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 1
        elif self.boxtype == '7220S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7210S':
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 2
        elif self.boxtype == '7005S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 1
        elif self.boxtype == '7225S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7215S':
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 2
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            if type == 'DVB-T2' or type == 'DVB-T':
                self.tuner_nr  = 3
        return False

    def closeFrontend(self, force = False):
        if self.raw_channel or force:
            if self.raw_channel:
                del self.raw_channel
                self.raw_channel = None
            if self.frontend:
                self.frontend.closeFrontend(True, True)
        return False

    def tuneSatellite(self, retune = 0):
        cnt = 0
        found = False
        for x in self.xmlFiles['satellite']:
            if x[0] == self.location.lower():
                if cnt == self.tune_index:
                    found = True
                    break
                cnt += 1

        if found:
            print x
            parm = eDVBFrontendParametersSatellite()
            parm.frequency = int(x[2]) * 1000
            parm.symbol_rate = int(x[3]) * 1000
            parm.polarisation = int(x[4])
            parm.fec = int(x[5])
            parm.inversion = int(x[6])
            parm.orbital_position = int(x[7])
            parm.system = int(x[8])
            parm.modulation = int(x[9])
            parm.rolloff = int(x[10])
            parm.pilot = int(x[11])
            feparm = eDVBFrontendParameters()
            feparm.setDVBS(parm, False)
            if self.frontend is not None:
                print '>>>>>>>>>>>>>>   tuneSatellite:: tune     <<<<<<<<<<<<<<<<'
                self.frontend.tune(feparm)
            print '>>>>>>>>>>>>>>   tuneSatellite:: tune done     <<<<<<<<<<<<<<<<'
            if int(x[4]) == 0:
                pol = 'HORIZONTAL'
            else:
                pol = 'VERTICAL'
            if int(x[13]) == 1:
                lnb = 'ON'
            else:
                lnb = 'OFF'
            if self.type_test == self.TEST_TUNER:
                self.showMessage()
                self.tune_text = 'Tuner %d %s(%s) Test Running\n\n%s\nFrequency: %s MHz, Symbol Rate: %s\nPolarity: %s, 22kHz: %s\n' % (self.tuner_nr + 1,
                 self.tuners[self.tuner_nr][0],
                 self.tuners[self.tuner_nr][1],
                 x[1],
                 x[2],
                 x[3],
                 pol,
                 lnb)
                if retune == 0:
                    if self.tune_index + 1 == self.getCount('satellite', self.location.lower()):
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to stop')
                    else:
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to next')
                elif self.tune_index + 1 == self.getCount('satellite', self.location.lower()):
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to stop')
                else:
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to next')

    def tuneCable(self, retune = 0):
        cnt = 0
        found = False
        for x in self.xmlFiles['cable']:
            if x[0] == self.location.lower():
                if cnt == self.tune_index:
                    found = True
                    break
                cnt += 1

        if found:
            modulation = ''
            if x[4] == '0':
                modulation = 'Auto'
            elif x[4] == '1':
                modulation = 'QAM16'
            elif x[4] == '2':
                modulation = 'QAM32'
            elif x[4] == '3':
                modulation = 'QAM64'
            elif x[4] == '4':
                modulation = 'QAM128'
            elif x[4] == '5':
                moduleation = 'QAM256'
            parm = eDVBFrontendParametersCable()
            parm.frequency = int(x[2]) * 1000
            parm.symbol_rate = int(x[3]) * 1000
            parm.modulation = int(x[4])
            parm.fec_inner = int(x[5])
            parm.inversion = int(x[6])
            parm.system = int(x[7])
            feparm = eDVBFrontendParameters()
            feparm.setDVBC(parm)
            if self.frontend is not None:
                self.frontend.tune(feparm)
            if self.type_test == self.TEST_TUNER:
                self.showMessage()
                self.tune_text = 'Tuner %d %s(%s) Test Running\n\n%s\nFrequency: %s MHz, Symbol Rate: %s\nModulation: %s\n' % (self.tuner_nr,
                 self.tuners[self.tuner_nr][0],
                 self.tuners[self.tuner_nr][1],
                 x[1],
                 x[2],
                 x[3],
                 modulation)
                if retune == 0:
                    if self.tune_index + 1 == self.getCount('cable', self.location.lower()):
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to stop')
                    else:
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to next')
                elif self.tune_index + 1 == self.getCount('cable', self.location.lower()):
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to stop')
                else:
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to next')

    def tuneTerrestrial(self, retune = 0):
        cnt = 0
        found = False
        for x in self.xmlFiles['terrestrial']:
            if x[0] == self.location.lower():
                if cnt == self.tune_index:
                    found = True
                    break
                cnt += 1

        if found:
            print x
            band = 0
            bandwidth = ''
            modulation = ''
            if x[4] == '0':
                bandwidth = '8MHz'
                band = 8000000
            elif x[4] == '1':
                bandwidth = '7MHz'
                band = 7000000
            elif x[4] == '2':
                bandwidth = 'Auto'
            elif x[4] == '3':
                bandwidth = '5MHz'
                band = 5000000
            elif x[4] == '4':
                bandwidth = '1.712MHz'
                band = 1712000
            elif x[4] == '5':
                bandwidth = '10MHz'
                band = 10000000
            if x[7] == '0':
                modulation = 'QPSK'
            elif x[7] == '1':
                modulation = 'QAM16'
            elif x[7] == '2':
                modulation = 'QAM64'
            elif x[7] == '3':
                modulation = 'Auto'
            elif x[7] == '4':
                modulation = 'QAM256'
            parm = eDVBFrontendParametersTerrestrial()
            parm.frequency = int(x[2]) * 1000
            parm.inversion = int(x[3])
            parm.bandwidth = band
            parm.code_rate_HP = int(x[5])
            parm.code_rate_LP = int(x[6])
            parm.modulation = int(x[7])
            parm.transmission_mode = int(x[8])
            parm.guard_interval = int(x[9])
            parm.hierarchy = int(x[10])
            parm.system = int(x[11])
            parm.plpid = int(x[12])
            feparm = eDVBFrontendParameters()
            feparm.setDVBT(parm)
            if self.frontend is not None:
                self.frontend.tune(feparm)
            if self.type_test == self.TEST_TUNER:
                self.showMessage()
                self.tune_text = 'Tuner %d %s(%s) Test Running\n\n%s\nFrequency: %d MHz, Band Width: %s\nConstellation: %s\n' % (self.tuner_nr,
                 self.tuners[self.tuner_nr][0],
                 self.tuners[self.tuner_nr][1],
                 x[1],
                 int(x[2]) / 1000,
                 bandwidth,
                 modulation)
                if retune == 0:
                    if self.tune_index + 1 == self.getCount('terrestrial', self.location.lower()):
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to stop')
                    else:
                        self['message'].setText(self.tune_text + '\nLockstate: not locked\n\nPress OK to next')
                elif self.tune_index + 1 == self.getCount('terrestrial', self.location.lower()):
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to stop')
                else:
                    self['message'].setText(self.tune_text + '\nLockstate: Locked\n\nPress OK to next')

    def setRightMenuUsb(self, slot, val):
        idx = slot
        if val is True:
            self['menuright' + str(idx)].setForegroundColorNum(1)
            self['menuright' + str(idx)].setBackgroundColorNum(1)
            self['menuright' + str(idx)].setText(' USB %s - OK' % self.usbslot_names[slot])
        else:
            self['menuright' + str(idx)].setForegroundColorNum(0)
            self['menuright' + str(idx)].setBackgroundColorNum(0)
            self['menuright' + str(idx)].setText(' USB %s' % self.usbslot_names[slot])

    def setRightMenuSmartcard(self, slot, val):
        idx = self.usbslots
        if slot == 0:
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' SMARTCARD A - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' SMARTCARD A')
        else:
            idx = idx + 1
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' SMARTCARD B - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' SMARTCARD B')

    def setRightMenuEthernet(self, slot, val):
        if slot == 0:
            idx = self.usbslots + self.scislots
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' ETHERNET A - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' ETHERNET A')
        else:
            idx = self.usbslots + self.scislots + 1
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' ETHERNET B - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' ETHERNET B')

    def setRightMenuSecurity(self, val):
        idx = self.usbslots + self.scislots + 1
        if self.has_eth1 is True:
            idx = idx + 1
        if val is True:
            self['menuright' + str(idx)].setForegroundColorNum(1)
            self['menuright' + str(idx)].setBackgroundColorNum(1)
            self['menuright' + str(idx)].setText(' SECURITY CHIP - OK')
        else:
            self['menuright' + str(idx)].setForegroundColorNum(0)
            self['menuright' + str(idx)].setBackgroundColorNum(0)
            self['menuright' + str(idx)].setText(' SECURITY CHIP')

    def setRightMenuCi(self, slot, val):
        idx = self.scislots + self.usbslots + 1
        if self.has_security is True:
            idx = idx + 1
        if self.has_eth1 is True:
            idx = idx + 1
        if slot == 0:
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' CI A - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' CI A')
        else:
            idx = idx + 1
            if val is True:
                self['menuright' + str(idx)].setForegroundColorNum(1)
                self['menuright' + str(idx)].setBackgroundColorNum(1)
                self['menuright' + str(idx)].setText(' CI B - OK')
            else:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
                self['menuright' + str(idx)].setText(' CI B')

    def setRightMenuEsata(self, val):
        idx = self.usbslots + self.scislots + self.cislots + 1
        if self.has_security is True:
            idx = idx + 1
        if self.has_eth1 is True:
            idx = idx + 1
        if val is True:
            self['menuright' + str(idx)].setForegroundColorNum(1)
            self['menuright' + str(idx)].setBackgroundColorNum(1)
            if self.boxtype == 'et7500' or self.boxtype == 'et8500':
                self['menuright' + str(idx)].setText(' INT./EXT. ESATA - OK')
            else:
                self['menuright' + str(idx)].setText(' ESATA - OK')
        else:
            try:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
            except:
                pass
            if self.boxtype == 'et7500' or self.boxtype == 'et8500':
                self['menuright' + str(idx)].setText(' INT./EXT. ESATA')
            else:
                try:
                    self['menuright' + str(idx)].setText(' ESATA')
                except:
                    pass

    def setRightMenusata(self, val):
        idx = self.usbslots + self.scislots + self.cislots + 1
        if self.has_security is True:
            idx = idx + 1
        if self.has_eth1 is True:
            idx = idx + 1
        if self.has_esata is True:
            idx = idx + 1
        if val is True:
            self['menuright' + str(idx)].setForegroundColorNum(1)
            self['menuright' + str(idx)].setBackgroundColorNum(1)
            self['menuright' + str(idx)].setText(' SATA - OK')
        else:
            try:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
            except:
                pass
            try:
                self['menuright' + str(idx)].setText(' SATA')
            except:
                pass
                
    def setRightMenuSDcard(self, val):
        idx = self.usbslots + self.scislots + self.cislots + 1
        if self.has_security is True:
            idx = idx + 1
        if self.has_eth1 is True:
            idx = idx + 1
        if self.has_esata is True:
            idx = idx + 1
        if self.has_sata is True:
            idx = idx + 1
            
        if val is True:
            self['menuright' + str(idx)].setForegroundColorNum(1)
            self['menuright' + str(idx)].setBackgroundColorNum(1)
            self['menuright' + str(idx)].setText(' SDCARD - OK')
        else:
            try:
                self['menuright' + str(idx)].setForegroundColorNum(0)
                self['menuright' + str(idx)].setBackgroundColorNum(0)
            except:
                pass
            try:
                self['menuright' + str(idx)].setText(' SDCARD')
            except:
                pass

    def setButton(self, val):
        if val >= 0:
            self['button' + str(val)].setForegroundColorNum(1)
            self['button' + str(val)].setBackgroundColorNum(1)

    def setMenuItem(self, val):
        for x in range(self.total_left):
            if val == x:
                if x in self.menu_tuner_index:
                    idx = x - self.menu_tuner_index[0]
                    if self.tuners[idx][0] == 'Unknown':
                        self.showTunerInfo(0, idx)
                        self['menuleft' + str(x)].setForegroundColorNum(2)
                    else:
                        self.showTunerInfo(1, idx)
                        self['menuleft' + str(x)].setForegroundColorNum(1)
                else:
                    self.hideTunerInfo()
                self['menuleftbox' + str(x)].setForegroundColorNum(1)
                self['menuleftbox' + str(x)].setBackgroundColorNum(1)
            else:
                self['menuleft' + str(x)].setForegroundColorNum(0)
                self['menuleftbox' + str(x)].setForegroundColorNum(0)
                self['menuleftbox' + str(x)].setBackgroundColorNum(0)

    def showTunerInfo(self, val, index):
        if val == 0:
            self['tunerinfo'].setText(' No Installed Tuner')
        else:
            self['tunerinfo'].setText(' ' + self.tuners[index][0] + ' (' + self.tuners[index][1] + ')')
        self['tunerinfo'].show()

    def hideTunerInfo(self):
        self['tunerinfo'].hide()
        self['tunerinfo'].setText('')

    def showMessage(self):
        self['message'].show()
        self['message_header'].show()

    def hideMessage(self):
        self['message'].hide()
        self['message_header'].hide()
        self['message'].setText('')

    def keyNumberGlobal(self, number):
        if number not in range(self.total_left):
            return
        if self.boxtype == 'et10000':
            if number == 0:
                self.leftmenu_idx = 9
            else:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'g300':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'et8000':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'et9x00':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'et7000':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'et7500':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == 'et8500':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == '7000S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7210S' or self.boxtype == '7220S':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == '7005S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7215S' or self.boxtype == '7225S':
            if number != 0:
                self.leftmenu_idx = number - 1
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            if number != 0:
                self.leftmenu_idx = number - 1
        else:
            return
        self.setMenuItem(self.leftmenu_idx)

    def keyOk(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_HDMI_IN:
                self.runHdmiTest(0)
            elif self.type_test == self.TEST_AGING:
                self.runAgingTest(0)
            elif self.type_test == self.TEST_TUNER:
                self.tune_index += 1
                self.runNextTunerTest()
            elif self.type_test == self.TEST_HDD:
                if self.record_end is True and self.record_play_start is False:
                    self.runHDDTest(2)
                else:
                    self.runHDDTest(0)
            elif self.type_test == self.TEST_SCART:
                self.runScartTest(0)
            elif self.type_test == self.TEST_FRONT_LED:
                if self.ledtest:
                    self.runFrontLEDTest(1)
                else:
                    self.runFrontLEDTest(0)
            return
        if self.TEST_KEYS is True:
            if self.boxtype == 'et8000' or self.boxtype == 'et10000' or self.boxtype == 'g300':
                self.setButton(self.buttons['ok'])
                if self.runKeyTestStart == False:
                    self.runKeyTest(0)
                self.runKeyTestStart = False
            elif self.boxtype == 'et9x00':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == 'et7000':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == 'et7500':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == 'et8500':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == '7000S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7300S' or self.boxtype == '7400S' or self.boxtype == '7210S':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == '7220S':
                self.setButton(self.buttons['ok'])
                self.front_ok_key_idx = self.front_ok_key_idx + 1
                if self.front_ok_key_idx > 6:
                    self.runKeyTestStart = False
                    self.runKeyTest(0)
            elif self.boxtype == '7005S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7305S' or self.boxtype == '7405S' or self.boxtype == '7215S':
                self.runKeyTestStart = False
                self.runKeyTest(0)
            elif self.boxtype == '7225S':
                self.setButton(self.buttons['ok'])
                self.front_ok_key_idx = self.front_ok_key_idx + 1
                if self.front_ok_key_idx > 6:
                    self.runKeyTestStart = False
                    self.runKeyTest(0)
            elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
                self.setButton(self.buttons['ok'])
                self.front_ok_key_idx = self.front_ok_key_idx + 1
                if self.front_ok_key_idx > 5:
                    self.runKeyTestStart = False
                    self.runKeyTest(0)
            return
        tuner_count = len(self.menu_tuner_index)
        if self.boxtype == 'et10000':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runHDDTest(1)
            elif self.leftmenu_idx == tuner_count + 1:
                self.runScartTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runHdmiTest(1)
            elif self.leftmenu_idx == tuner_count + 3:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 4:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 5:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 6:
                self.runRemovePlugin()
        elif self.boxtype == 'et8000':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runHDDTest(1)
            elif self.leftmenu_idx == tuner_count + 1:
                self.runScartTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 3:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 4:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 5:
                self.runRemovePlugin()
        elif self.boxtype == 'g300':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 3:
                self.runRemovePlugin()
        elif self.boxtype == 'et9x00':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runHDDTest(1)
            elif self.leftmenu_idx == tuner_count + 1:
                self.runScartTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 3:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 4:
                self.runRemovePlugin()
        elif self.boxtype == 'et7000':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == 'et7500':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == 'et8500':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runAgingTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == '7000S' or self.boxtype == '7100S' or self.boxtype == '7200S' or self.boxtype == '7300S' or self.boxtype == '7400S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == '7210S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runScartTest(1)
            elif self.leftmenu_idx == tuner_count + 1:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 2:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 3:
                self.runRemovePlugin()
        elif self.boxtype == '7220S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.front_ok_key_idx = 0
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == '7005S' or self.boxtype == '7105S' or self.boxtype == '7205S' or self.boxtype == '7305S' or self.boxtype == '7405S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == '7215S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.runScartTest(1)
            elif self.leftmenu_idx == tuner_count + 1:
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 2:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 3:
                self.runRemovePlugin()
        elif self.boxtype == '7225S':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.front_ok_key_idx = 0
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()
        elif self.boxtype == '8100S' or self.boxtype == 'e4hd' or self.boxtype == 'protek4k' or self.boxtype == 'hd61':
            if self.leftmenu_idx in self.menu_tuner_index:
                self.runTunerTest(1)
            elif self.leftmenu_idx == tuner_count:
                self.front_ok_key_idx = 0
                self.runKeyTest(1)
                self.runKeyTestStart = True
            elif self.leftmenu_idx == tuner_count + 1:
                self.runFrontLEDTest(1)
            elif self.leftmenu_idx == tuner_count + 2:
                self.runRemovePlugin()

    def keyUp(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_TUNER:
                self.runTunerTest(0)
            elif self.type_test == self.TEST_HDD:
                self.runAgingTestKeyActionProtect = True
                self.runHDDTest(0)
            elif self.type_test == self.TEST_FRONT_LED:
                self.runAgingTestKeyActionProtect = True
                self.runFrontLEDTest(0)
            else:
                return
        if self.type_test == self.TEST_SCART:
            self.runAgingTestKeyActionProtect = True
            self.runScartTest(0)
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['up'])
            return
        if self.leftmenu_idx > 0:
            self.leftmenu_idx = self.leftmenu_idx - 1
        else:
            self.leftmenu_idx = self.total_left - 1
        self.setMenuItem(self.leftmenu_idx)

    def keyDown(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_TUNER:
                self.runTunerTest(0)
            elif self.type_test == self.TEST_HDD:
                self.runAgingTestKeyActionProtect = True
                self.runHDDTest(0)
            elif self.type_test == self.TEST_FRONT_LED:
                self.runAgingTestKeyActionProtect = True
                self.runFrontLEDTest(0)
            else:
                return
        if self.type_test == self.TEST_SCART:
            self.runAgingTestKeyActionProtect = True
            self.runScartTest(0)
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['down'])
            return
        if self.leftmenu_idx < self.total_left - 1:
            self.leftmenu_idx = self.leftmenu_idx + 1
        else:
            self.leftmenu_idx = 0
        self.setMenuItem(self.leftmenu_idx)

    def keyLeft(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['left'])
            return

    def keyRight(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['right'])
            return

    def keyVolumeDown(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.front_ok_key_idx = self.front_ok_key_idx + 1
            self.setButton(self.buttons['voldown'])
            return

    def keyVolumeUp(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.front_ok_key_idx = self.front_ok_key_idx + 1
            self.setButton(self.buttons['volup'])
            return

    def keyChannelDown(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.front_ok_key_idx = self.front_ok_key_idx + 1
            self.setButton(self.buttons['channeldown'])
            return

    def keyChannelUp(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.front_ok_key_idx = self.front_ok_key_idx + 1
            self.setButton(self.buttons['channelup'])
            return

    def keyPower(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.front_ok_key_idx = self.front_ok_key_idx + 1
            self.setButton(self.buttons['power'])
            return

    def keyCancel(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_TUNER or self.type_test == self.TEST_REMOVE:
                if self.type_test == self.TEST_TUNER:
                    self.runTunerTest(0)
                elif self.type_test == self.TEST_REMOVE:
                    self['buttons_blue'].hide()
                self.hideMessage()
                self.type_test = self.TEST_NONE
                self.want_ok = False
            return
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['cancel'])
            return

    def keyMenu(self):
        if self.want_ok is True:
            return
        if self.TEST_KEYS is True:
            self.setButton(self.buttons['menu'])
            return

    def keyRed(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_TUNER:
                self.runTunerTest(0)
                self.type_test = self.TEST_NONE
                self.want_ok = False
            else:
                return
        if self.location_idx < len(self.locations) - 1:
            self.location_idx = self.location_idx + 1
        else:
            self.location_idx = 0
        self.location = self.locations[self.location_idx]
        self['stbname'].setText(' %s - %s' % (self.boxtype.upper(), self.location.upper()))

    def keyYellow(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_TUNER:
                self.runTunerTest(0)
                self.type_test = self.TEST_NONE
                self.want_ok = False
            else:
                return
        self.runAgingTestKeyActionProtect = True
        self.runAgingTest(1)

    def keyBlue(self):
        if self.want_ok is True:
            if self.type_test == self.TEST_REMOVE:
                self.doRemoveFactoryTest()

    def readMainXml(self):
        xmlnode = []
        xmlnode = xml.dom.minidom.parse('/usr/lib/enigma2/python/Plugins/Extensions/FactoryTest/list.xml')
        tmp = xmlnode.getElementsByTagName('satellite')[0].getElementsByTagName('transponder')
        if len(tmp) > 0:
            self.xmlFiles['satellite'] = []
        for i in range(len(tmp)):
            location = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('location')[0].childNodes))
            description = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('description')[0].childNodes))
            frequency = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('frequency')[0].childNodes))
            symbolrate = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('symbolrate')[0].childNodes))
            polarization = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('polarization')[0].childNodes))
            fec = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('fec')[0].childNodes))
            inversion = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('inversion')[0].childNodes))
            satpos = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('satpos')[0].childNodes))
            system = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('system')[0].childNodes))
            modulation = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('modulation')[0].childNodes))
            rolloff = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('rolloff')[0].childNodes))
            pilot = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('pilot')[0].childNodes))
            band = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('band')[0].childNodes))
            khz = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('khz')[0].childNodes))
            service = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('service')[0].childNodes))
            if location not in self.locations:
                self.locations.append(location)
            self.xmlFiles['satellite'].append((location,
             description,
             frequency,
             symbolrate,
             polarization,
             fec,
             inversion,
             satpos,
             system,
             modulation,
             rolloff,
             pilot,
             band,
             khz,
             service))

        tmp = xmlnode.getElementsByTagName('cable')[0].getElementsByTagName('transponder')
        if len(tmp) > 0:
            self.xmlFiles['cable'] = []
        for i in range(len(tmp)):
            location = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('location')[0].childNodes))
            description = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('description')[0].childNodes))
            frequency = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('frequency')[0].childNodes))
            symbolrate = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('symbolrate')[0].childNodes))
            modulation = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('modulation')[0].childNodes))
            fec_inner = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('fec_inner')[0].childNodes))
            inversion = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('inversion')[0].childNodes))
            system = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('system')[0].childNodes))
            service = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('service')[0].childNodes))
            if location not in self.locations:
                self.locations.append(location)
            self.xmlFiles['cable'].append((location,
             description,
             frequency,
             symbolrate,
             modulation,
             fec_inner,
             inversion,
             system,
             service))

        tmp = xmlnode.getElementsByTagName('terrestrial')[0].getElementsByTagName('transponder')
        if len(tmp) > 0:
            self.xmlFiles['terrestrial'] = []
        for i in range(len(tmp)):
            location = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('location')[0].childNodes))
            description = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('description')[0].childNodes))
            frequency = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('frequency')[0].childNodes))
            inversion = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('inversion')[0].childNodes))
            bandwidth = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('bandwidth')[0].childNodes))
            coderateHP = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('coderateHP')[0].childNodes))
            coderateLP = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('coderateLP')[0].childNodes))
            modulation = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('modulation')[0].childNodes))
            transmission = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('transmission')[0].childNodes))
            gard = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('gard')[0].childNodes))
            hierarchy = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('hierarchy')[0].childNodes))
            system = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('system')[0].childNodes))
            plpid = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('plpid')[0].childNodes))
            service = self.stripLineEndings(self.getText(tmp[i].getElementsByTagName('service')[0].childNodes))
            if location not in self.locations:
                self.locations.append(location)
            self.xmlFiles['terrestrial'].append((location,
             description,
             frequency,
             inversion,
             bandwidth,
             coderateHP,
             coderateLP,
             modulation,
             transmission,
             gard,
             hierarchy,
             system,
             plpid,
             service))

    def stripLineEndings(self, buf):
        return buf.strip('\r\n').strip('\n').strip('\t')

    def getText(self, nodelist):
        rc = []
        for node in nodelist:
            if node.nodeType == node.TEXT_NODE:
                rc.append(node.data)
            return str(''.join(rc))

    def getCount(self, type, target):
        cnt = 0
        for x in self.xmlFiles[type]:
            if x[0] == target:
                cnt += 1

        return cnt

    def readlog(self, slot):
        ret = ''
        if os.path.exists('/var/log/messages'):
            size = os.path.getsize('/var/log/messages')
            if size != self.last_message_size[slot]:
                if size < self.last_message_size[slot]:
                    self.last_message_size[slot] = 0
                fd = open('/var/log/messages')
                fd.seek(self.last_message_size[slot], 1)
                ret = fd.read()
                fd.close()
                if self.last_message_size[slot] == 0:
                    self.last_message_size[slot] = size
                    return ''
                self.last_message_size[slot] = size
        return ret.split('\n')

    def readEsatalog(self):
        ret = ''
        if os.path.exists('/var/log/messages'):
            size = os.path.getsize('/var/log/messages')
            if size != self.last_esata_message_size:
                if size < self.last_esata_message_size:
                    self.last_esata_message_size = 0
                fd = open('/var/log/messages')
                fd.seek(self.last_esata_message_size, 1)
                ret = fd.read()
                fd.close()
                self.last_esata_message_size = size
        return ret.split('\n')

    def readSDcardlog(self):
        ret = ''
        if os.path.exists('/var/log/messages'):
            size = os.path.getsize('/var/log/messages')
            if size != self.last_sdcard_message_size:
                if size < self.last_sdcard_message_size:
                    self.last_sdcard_message_size = 0
                fd = open('/var/log/messages')
                fd.seek(self.last_sdcard_message_size, 1)
                ret = fd.read()
                fd.close()
                self.last_sdcard_message_size = size
        return ret.split('\n')
        
    def readFile(self, name):
        try:
            f = open(name, 'r')
            lines = f.read().strip()
            f.close()
            return lines
        except:
            return ''

    def fanControl(self, value):
        f = open('/proc/stb/fp/fan', 'w')
        f.write(value)
        f.close()

    def doRemoveFactoryTest(self):
        if self.boxtype == 'et8000' or self.boxtype == 'et10000':
            os.system('rm -fR /etc/enigma2/lamedb')
            os.system('cp /etc/enigma2/lamedb_org /etc/enigma2/lamedb')
            os.system('rm -fR /etc/enigma2/userbouquet.LastScanned.tv')
            os.system('mv /etc/enigma2/userbouquet.LastScanned.tv_org /etc/enigma2/userbouquet.LastScanned.tv')
            os.system('rm -fR /etc/enigma2/bouquets.tv')
            os.system('mv /etc/enigma2/bouquets.tv_org /etc/enigma2/bouquets.tv')
            os.system('rm -fR /etc/enigma2/settings')
            os.system('rm -fR /etc/enigma2/satellites.xml')
            if os.path.exists('/etc/enigma2/satellites.xml.factory'):
                os.system('mv /etc/enigma2/satellites.xml.factory /etc/enigma2/satellites.xml')
        else:
            os.system('rm -fR /etc/enigma2')
        os.system('rm -fR /etc/init.d/prepare-factorytest')
        os.system('rm -fR /etc/rc3.d/S90prepare-factorytest')
        os.system('rm -fR /usr/lib/enigma2/python/Plugins/Extensions/FactoryTest')
        if self.boxtype == 'et8000' or self.boxtype == 'et10000' or self.boxtype == 'et8500':
            if os.path.exists('/proc/stb/fp/fan'):
                self.fanControl('off')
        if self.has_eth1 is True:
            os.system('ifdown eth1')
        os.system('opkg remove enigma2-plugin-extensions-factory --autoremove')
        os._exit(0)


def timerCallback():
    global g_timerinstance
    global g_session
    g_timerinstance.stop()
    g_session.open(cFactoryTestPlugin)


def autostart(session, **kwargs):
    global g_timerinstance
    global g_session
    g_session = session
    g_timerinstance = eTimer()
    g_timerinstance.callback.append(timerCallback)
    g_timerinstance.start(1000)


def Plugins(**kwargs):
    return [PluginDescriptor(where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)]
