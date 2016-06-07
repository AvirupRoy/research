# -*- coding: utf-8 -*-
"""
Perform OCR on the menu screenshots downloaded from the SR785,
building up a data-structure with the gathered information
Created on Thu Jan 07 10:32:40 2016

@author: Felix Jaeckel <felix.jaeckel@wisc.edu>
"""

from SR785_MenuAnalyzer import MenuImageAnalyzer
import PyQt4.QtGui as gui
from PIL import Image                   # QImage can't handle the GIFs we get, so use PIL
#from PIL import ImageFile               # Some images are truncated, so ...
#ImageFile.LOAD_TRUNCATED_IMAGES = True  # allow loading of truncated images
#from io import BytesIO
from SR785 import SR785
import pytesseract as ocr

def ocrQImage(image):
    image.save('tempOcr.png')
    im = Image.open('tempOcr.png')
    return ocr.image_to_string(im, lang='eng', config='-psm 7')

menuKeys = SR785.MenuKeyMap

app = gui.QApplication([])

def extractMenu(name, path):    
    print "Name, path:", name, path
    fileName = '%s#%s.png' % (name, '_'.join([str(x) for x in path]))
    image = gui.QImage(fileName)
    print "Image:", image.width(), image.height()
    try:
        analyzer = MenuImageAnalyzer(image)
    except:
        return []
    ocrHeader = ocrQImage(analyzer.headerImage())    
    print "Menu header:", ocrHeader
    items = []
    subMenus = []
    for i in range(10):
        itemType = analyzer.itemType(i)
        ocrHeading = ocrQImage(analyzer.itemHeadingImage(i))
        itemType = analyzer.itemType(i)
        print "Item:", i, '"%s"' % ocrHeading, "Type:", itemType
        items.append((i, analyzer.headingHashes[i], analyzer.heading(i), itemType, ocrHeading))

        if analyzer.isSubMenu(i) and analyzer.isEnabled(i):
            softKeyCode = SR785.SoftKeyMap[i+1]
            p = path[:]
            p.append(softKeyCode)
            subMenuName = '%s_%s' % (name, ocrHeading)
            sub = extractMenu(subMenuName, p)
            subMenus.append(sub)

    menu = [path, ocrHeader, analyzer.headerHash, items, subMenus]            
    return menu
    

menus = []
for x in menuKeys:
    menuName = x[0].replace('\n',' ')
    keyCode = x[1]
    path = [keyCode]
    name = 'MenuScreenshots/Menu_%s' % menuName
    menu = extractMenu(name, path)
    menus.append(menu)

from pprint import pformat
with open('SR785_Menus_Raw.py', 'a') as f:
    f.write(pformat(menus, indent=4, width=200))
    
#    
    #print headerHash
#    print "Header:", header
    
#    items = []
#    for i in range(10):
#        menuType = analyzer.menuType(i)
#        if menuType is not None:
#            ocrHeading = ocrQImage(analyzer.menuHeadingImage(i))
#            items.append((i, analyzer.headingHashes[i], menuType, ocrHeading))
#            print i, analyzer.headingHashes[i], ocrHeading,',', menuType
#            
#    menus[menu] = (headerHash, header, items)
#
#menus = {'Menu_System_DateTime': ('c5a83efa0a1a70a067fe9801fe73795aad1720fa', 'Time', 
#                                  [(2, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')])
#         'Menu_System_Diagnostics_Memory': ('3600290010aef50c267717a32b7ad2f8d35f574b', 'Memory Tests',
#                                [(0, '9df39db80d4adcd0ed68313748a58352d6f2b216', 'SubMenu', 'System RAM'), (1, 'f8b80c4fd09342a879cd6ad5f0229dfde551a4e2', 'SubMenu', 'System ROM'), (2, 'f6044ef1442636b20bfbc664662f0edee82fd3b8', 'SubMenu', '\\\xef\xac\x81deo RAM'), (3, '9127c745e6061f90b928bbe57be4dc0434acdcf5', 'SubMenu', 'Help ROM'), (4, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_System_Remote': ('b623105103231509183bc7f40328d24abfe03b37', 'Remote', [(6, 'c3f6528f0ee8d67cf4fe3a8edf0b32d56ea374f0', 'ButtonUnchecked', '\\\xef\xac\x81ew Qs'), (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Frequency': ('aa50e561439bfe6a1a945909fc03292ba980464e', 'Frequency', [(3, '476de5cb278b5a9520d4486f2867a19eee554bce', 'ButtonUnchecked', 'Full Span')]), 'Menu_Input_TransducerUnits': ('bbeb6f78920082728ac3b7677cc9e2640bcc62a7', 'Transducer Units', [(4, '5ebbbe1d5110ecddf21c7ee1dfc464365da31182', 'ButtonUnchecked', ''), (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Arb_More_Allocate': ('24fa1e61278232ce2b7a0115fe109503cf835ff2', 'Memory Allocation', [(4, '94f5f1702d19853f3acb0a04e649534f33e4160e', 'ButtonUnchecked', 'Con\xef\xac\x81rm Allocation'), (5, '2a926b3594f9b807619b49b461a31442a3f8042f', 'ButtonUnchecked', 'Clear Allocation'), (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Analysis_CurveFit': ('a855974c9ba95cc4067b31185df7a10102e1b0e1', 'Curve Fit', [(0, 'b84c9c0d197878faf4c1732a6063f3cdd2842df5', 'ButtonUnchecked', 'Start Fit'), (1, '690f8088b3570b8cb921be41ea6cad511c30a7b4', 'ButtonUnchecked', 'Abort Fit'), (2, '1767cffcd6031dbcf4ee19e1fc1bd8f8f6ae87ca', 'ButtonUnchecked', 'synthesize Tb|.1'), (3, '76118df8b5bb8e121131c11d308f59b656274e3b', 'ButtonUnchecked', 'synthesize Tbl.2'), (4, '7c885a9000948151f3f376859a666c2d63c594eb', 'SubMenu', 'Fit setup'), (6, 'fbf8fb321673d3a0d9ebeb260edff6c1b27c7178', 'SubMenu', ''), (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Analysis': ('49ae92a0ba80a7290de84d7b59eaf4b580204018', 'Analysis', [(0, '444aeb605294dec439d947f7906afd4d50809316', 'SubMenu', 'Data Table'), (1, 'ddbb2a1f19b6b9ae8ca2fd6a3fe7e8b48627da33', 'SubMenu', 'Limit Test'), (2, 'bcd7ba0f1c44b8bec89375aba0639f63e1dfd060', 'SubMenu', 'Marker Stats.'), (3, '00bcd9d221fb9b7718d47597c4ed396826ebb057', 'SubMenu', 'Exceedance Stats.'), (4, '98efffeff072ed245ea4910f32ad0bd263a673f2', 'SubMenu', 'Curve Fit')]), 'Menu_System_Diagnostics': ('590d8f294cb00f4da5b461b225e40fa36b6e8769', 'Test', [(0, '63ea621e5e3a3dc4c48efdc9cbccec925212c1f7', 'ButtonUnchecked', 'Keypad'), (1, 'd1f5cd35e282774dad578370be4cad5e466c6b9c', 'ButtonUnchecked', 'Keyboard'), (2, '6267778df5ac1c0fb8331c158064042b6480adc3', 'SubMenu', 'Knob'), (3, 'a621b03ca6f568fb454c470f21483665399909bc', 'SubMenu', 'R8232 I P rinter'), (4, '3df4282c08641bb8662ffb97148dd3bc27434771', 'SubMenu', 'Memory'), (5, '0570d01c3b1d9d8e2a079db3b4f0b9aa6d608484', 'SubMenu', 'Disk'), (7, 'dbb526c39904b8ff67c4c393215964ff9a360401', 'ButtonUnchecked', 'Program SIN'), (8, '54b3b69e491d1253474f43c1529811ec39c91460', 'ButtonUnchecked', 'Kill Autonf')]), 'Menu_Waterfall_More': ('a31e9509b6ff7ce11a1aa7ffc232cdf8964797c7', 'Waterfall', [(5, '549a634e87638d1b1777e073b31c14c844f5d8cb', 'ButtonUnchecked', 'Record (0 Trace'), (6, '6a877ada6e25896f9132ce9a4eab11a5ce0f0671', 'ButtonUnchecked', 'Slice (0 Trace'), (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Capture': ('74ae44dc6b0fcec31397ca872dcbd3b0083b2bc4', 'Capture', [(5, 'fdceaf9c9fb4ded1567b106e913adde64a55f06c', 'SubMenu', 'Allocate Mem.'), (6, 'aaa675a8e7836caa266cecda80a6cc2967ed35e8', 'ButtonUnchecked', '\\\xef\xac\x81ew Header')]), 'Menu_Analysis_LimitTesting': ('0a7f1e2a2685e9327762072cd6aea1fd6e574ed5', 'Limit Testing', [(3, '5e50dcf3351254a59950e5e7ec4d702fdf81216f', 'ButtonUnchecked', 'Clear Limits'), (4, '71e0cddfb494adad07192d303159c38a3a402342', 'SubMenu', 'Edit Limits'), (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Disk_Buffers': ('c6a464f3bee47a9d9a58390b15bbebcab5d3b865', 'Buffers', [(2, '1df0287e02e63a06417e6082a283c60d40d5c2a5', 'ButtonUnchecked', 'Ld Trc Data (Ascii)'), (3, 'd583cb1648da5ccf71f7b0e94354584214453114', 'ButtonUnchecked', 'Ld Trc Data (Bin)'), (6, '0136a9947b262f0ff724add245e387bbdc0b5a00', 'ButtonUnchecked', 'Disk (0 Buffer'), (7, '7e705816c545214a8672064fdabcb7fbde18b19d', 'ButtonUnchecked', ''), (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Waterfall': ('a31e9509b6ff7ce11a1aa7ffc232cdf8964797c7', 'Waterfall', [(8, 'fdceaf9c9fb4ded1567b106e913adde64a55f06c', 'SubMenu', 'Allocate Mem.'), (9, '021a1edbcd8dca8aa26200b40c1eea8e31d60c72', 'SubMenu', 'More .')]), 'Menu_Input': ('b8e55efd6b4225e96f9e5876f6e4733d09b62a48', 'Input', [(2, 'cdc1fdda49d3d479643570d9e6a7478edcf86a60', 'SubMenu', 'Input Con\xef\xac\x81g'), (3, '286868a4435efd582ea626dfe1139105ad139b23', 'SubMenu', 'Trnsdcr P arams.'), (4, '9ebc49d5d1f8ac18c0c108011e456dca63b45999', 'SubMenu', 'Tach Input'), (5, '33372e77346c857a3fba2730ce54d22b7d7519b3', 'SubMenu', 'Playback Con\xef\xac\x81g')]), 'Menu_Output_Colors': ('71db1b47afe2f94a44a1937f0fb5fb6e3928b45b', 'Hardcopy Colors', [(8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Chirp': ('df8f38bc656f09d2424624c57cee78daef512f83', 'Source', []), 'Menu_Analysis_DataTable': ('49554de55a66e26746029e8a4d63a7703a3d3d05', 'Data Table', [(1, 'ae0231c12c3c9884de99da68e83157fcaf692254', 'ButtonUnchecked', 'Insert Line'), (2, '923a07024aa8aeddef35960d4356d7e9bfe5b28d', 'ButtonUnchecked', 'Modify Line'), (3, 'd8f7ef7285abb4d64298ce32110d601811c31565', 'ButtonUnchecked', 'Delete Line'), (4, '4d55e1e24ea09eda252fb335e932d6070d60484a', 'ButtonUnchecked', 'Clear Table'), (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Trigger_RPMTimeArm': ('297e4836b602585ecc86092e6909a57f9f470937', 'RPMfTime Arm', [(5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Arb': ('df8f38bc656f09d2424624c57cee78daef512f83', 'Source', []), 'Menu_Disk_GetSettings': ('68db1e9ed77650346edf1f1e4890373e712f6ce6', 'Get Settings', [(2, '34a47acae3f2887e8b7b63c84abc8c4f6d12599d', 'ButtonChecked', 'Measurements'), (3, '77eac48e9cd225a008a58a486928b15e9073003d', 'ButtonChecked', 'Sources'), (4, '74a7b4ac46886431c4c0be51f65b5428f2b4ffe5', 'ButtonChecked', 'Analysis'), (5, '6a9099026c4b0ab4c8a866d37de84b420524f5f2', 'ButtonChecked', 'Inputszriggers'), (6, '732ba5ac276bf991b28759aff142595b6f9fa132', 'ButtonChecked', 'DRAM settings'), (7, '8b7973aecff39402793b39fc774507e158c4b43a', 'ButtonChecked', 'Gen. System'), (8, 'c9a7e055b4009c95ad5461c9bd4a7b3bbeb902ee', 'ButtonChecked', 'Macros'), (9, '7db40dcbc455b42c7e36db9517d3953fd15de7fb', 'ButtonUnchecked', 'Recall from Disk')]), 'Menu_DisplaySetup': ('af864451ff2a94647ffe4013bea66b4efc4ad103', 'Display Setup', [(3, '28744eb70503c4f665c37655d24d68236f1c18eb', 'SubMenu', 'Units')]), 'Menu_Disk_Upkeep': ('f37b6396133c7dcdc07564b95865a446d226dbcb', 'Disk Upkeep', [(4, '33a8026a36cdd2635e4bc082a80cb4332cda98bc', 'ButtonUnchecked', 'Del. File'), (5, 'fdf24e16c1456073262a10bb49a5b4516ad258a2', 'ButtonUnchecked', 'Del. cur. Dir'), (7, '7e98875903b47aaf216d02f8eb3507213e920774', 'ButtonUnchecked', 'Format Floppy')]), 'Menu_Averaging': ('c07f2077d62ebfc8bcac419f134636b8abb7ffdd', 'Averaging', [(5, '7c1eef631daaa8dd1a0af040423d3c50a087cb50', 'SubMenu', 'More'), (8, 'f3783e020d185fbc77e4974b2c9f0f2c82e73e37', 'ButtonUnchecked', '')]), 'Menu_System': ('a6b1b7bf0059412dba334c711ea86f6b1eef9a7c', 'System', [(0, 'd7bd7acd6662c2981bed17bb43f739776c82c437', 'ButtonUnchecked', 'P reset'), (1, '426f618b80b197435057bb39e86a3429d545be19', 'SubMenu', 'Remote'), (2, 'e7c6e10c58460dc2190cc981f9d2744c2277d3ab', 'SubMenu', 'P references'), (3, 'bb50a37eb62aa49158d90c0a78cfc4606b65048c', 'SubMenu', 'DatefTime'), (4, '81a1cd646e10c77a4e9ef8cf7ce62b5e31d43179', 'SubMenu', 'Diagnostics'), (6, '6cdf1fe9748c66d7f5c76fd8db3959d690445162', 'SubMenu', 'Edit Macro'), (7, '71d8e71eee0e7a96c38910541555286c4a607dfe', 'ButtonUnchecked', 'Show Settings'), (8, 'f05d903cb61b25ef8c9976d9ba77b6889305473a', 'ButtonUnchecked', 'Show Version')]), 'Menu_Input_PlaybackConfig': ('4002f79646496fb0ebaae79cd780e2a598a9d035', 'Playback Con\xef\xac\x81g', [(4, 'f2b119ada974fa25b965dabc1563686d23892c44', 'ButtonUnchecked', ''), (5, 'ff1971535ab7e5b1d4761abf24e0e2058408f383', 'ButtonUnchecked', ''), (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Analysis_CurveFit_FitSetup': ('bb95f9a49d6c2989b62a336649c537f770e32254', 'Fit setup', [(4, '754158687e4d7d976c6592f98e4b89bd9c2ddaef', 'ButtonUnchecked', 'Set Fit Rgn'), (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Capture_MemoryAllocation': ('24fa1e61278232ce2b7a0115fe109503cf835ff2', 'Memory Allocation', [(4, '94f5f1702d19853f3acb0a04e649534f33e4160e', 'ButtonUnchecked', 'Con\xef\xac\x81rm Allocation'), (5, '2a926b3594f9b807619b49b461a31442a3f8042f', 'ButtonUnchecked', 'Clear Allocation'), (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Noise': ('df8f38bc656f09d2424624c57cee78daef512f83', 'Source', []), 'Menu_System_Preferences': ('90db1a7766cb2521938408b93ea2eae6b9a6a452', 'P references', []), 'Menu_Input_InputConfig': ('c18071ba176a0b8091576c296790a8b347a1cb64', 'Input Con\xef\xac\x81g', [(8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Tone2': ('e519c275816cacbfc495ee860d6d4f36794cd0be', 'Tone 2', [(2, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Analysis_LimitTesting_EditLimits_Active': ('5dba64a625981ad7543212266b123021de5fc9bb', 'Edit Limits', [(0, 'c9d1ed8877bcd79fa1b446a089bbbac5424315fc', 'ButtonUnchecked', 'New Segment'), (7, 'a46618a8540c2dde313a47525a88c593857143f0', 'ButtonUnchecked', 'Delete Segment'), (9, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Trigger': ('e6c4bec9cb4af088a366a1d27990823d4e74b588', 'Trigger', [(7, '77e1bc67a28dab39022097f40027c0c4ee7e74d5', 'SubMenu', 'RPMfTime Setup'), (8, '1f7525d3a88c09a639694297674779bf8e74edc2', 'ButtonUnchecked', 'Manual Arm'), (9, 'aece5946f911714d4475dedeed505850de3903f3', 'ButtonUnchecked', 'Manual Trigger')]), 'Menu_Target': ('9aeb67e273b3211c069170c8014c7c6b68899e75', 'Marker Setup', [(8, 'e2c70e523af92a066efb5ef476c73b8c97ceca70', 'ButtonUnchecked', 'Marker X to')]), 'Menu_Averaging_More': ('7223408bae3d389c2d431e7368508a6dadfadf0f', 'More Options', [(2, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_System_Diagnostics_Memory_SystemRAM': ('1c4ca7c5897bf8ff5c06730a3ba4f9fe5a367230', 'System RAM', [(0, '9f0e24462170a5b1e1ee045841d35a4a85895bb6', 'ButtonUnchecked', 'Begin'), (1, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Source_Arb_More': ('6baa4ce12d589ca4e8886cb50f48fa35dd244daf', 'Arb. Src. Settings', [(4, 'f2b119ada974fa25b965dabc1563686d23892c44', 'ButtonUnchecked', ''), (5, 'ff1971535ab7e5b1d4761abf24e0e2058408f383', 'ButtonUnchecked', ''), (6, 'fdceaf9c9fb4ded1567b106e913adde64a55f06c', 'SubMenu', 'Allocate Mem.'), (7, 'e88e084c27f202e60f3b72264db0d5959d6942ce', 'ButtonUnchecked', 'Trace to Arb'), (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Output': ('558c5fd0bccf94a33780b253515a71bb74971e4c', 'Hardcopy Output', [(7, '3867b632f929de431460801c78c57e44b196cb79', 'ButtonUnchecked', 'Edit A Note'), (9, '38819d792603ef2495b6cfd52819b63bf32f91ca', 'SubMenu', 'Colors')]), 'Menu_Window_WindowForceExp': ('1ea6b787e24c6659146fb03ff3afc71ba6dc3177', 'Window', [(6, '3f97aee010f26e3f38fd0d53eb9ce6330a994900', 'ButtonUnchecked', 'Trace to Window'), (7, '1ddd4587fc67c8e60121bfc074907c861b6115e2', 'ButtonUnchecked', 'Window (0 Trace')]), 'Menu_Waterfall_MemoryAllocation': ('24fa1e61278232ce2b7a0115fe109503cf835ff2', 'Memory Allocation', [(4, '94f5f1702d19853f3acb0a04e649534f33e4160e', 'ButtonUnchecked', 'Con\xef\xac\x81rm Allocation'), (5, '2a926b3594f9b807619b49b461a31442a3f8042f', 'ButtonUnchecked', 'Clear Allocation'), (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_UserMath': ('384fe1216ea5b0804bd28b07fb4b4a0a0205f632', 'User Math', [(1, '557fd25ae1b36b615ca23667fdfbf0e18cdedbd4', 'SubMenu', 'Edit Fn.'), (2, '7c3e8ca1643ec65410da43398c66e092beaadd95', 'SubMenu', 'Edit Const')]), 'Menu_Analysis_LimitTesting_EditLimits': ('5dba64a625981ad7543212266b123021de5fc9bb', 'Edit Limits', [(0, 'c9d1ed8877bcd79fa1b446a089bbbac5424315fc', 'ButtonUnchecked', 'New Segment'), (7, '2ac63622cbec41a2a198aa0cba7c3afcd4a68b22', 'ButtonUnchecked', '')]), 'Menu_Analysis_MarkerStats': ('11d6b43ce5cc3ade98dec8e279be35d256d89ab9', 'Marker Statistics', [(1, 'f25b0564c523624917459e8f4929a2d2b2d785db', 'ButtonUnchecked', 'Reset')]), 'Menu_Window': ('1ea6b787e24c6659146fb03ff3afc71ba6dc3177', 'Window', [(6, '3f97aee010f26e3f38fd0d53eb9ce6330a994900', 'ButtonUnchecked', 'Trace to Window'), (7, '1ddd4587fc67c8e60121bfc074907c861b6115e2', 'ButtonUnchecked', 'Window (0 Trace')]), 'Menu_Analysis_Exceedance': ('7433c1a55a468f1df1ecf37d6fc538e8cc23f579', 'Exceedance', [(3, 'd84d9e17cd6c94d60664d0437e9acc7b1c500cc6', 'ButtonUnchecked', 'Calculate Excd.'), (4, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'ButtonUnchecked', 'Return')]), 'Menu_Disk': ('4cc88429816f534d82f4a8a412654af32509f9d6', 'Storage', [(2, '78782e0feacc0f54c58b06475002e6de996f44f3', 'ButtonUnchecked', 'Display to Disk'), (3, 'c43af6f9870e6928377f87e23e023ea5e69e090f', 'ButtonUnchecked', 'Disk to Display'), (4, '2e49480534dd10864061df161498555b7560d164', 'ButtonUnchecked', 'Settings (0 Disk'), (5, 'fdd5238b8696aeb12724c7f147cf2ece91e56251', 'SubMenu', 'Recall Settings'), (6, '36dd6a6bca7b6dc66b9be3a40240cbd4633a202a', 'ButtonUnchecked', 'Trace to Disk'), (7, 'cfb0e8e4f5fc4a0625cac94b7ce822d070d8152f', 'ButtonUnchecked', 'Disk (0 Trace'), (8, 'e21dbda7697bde2874df75dfcacaf7d1ac056a97', 'SubMenu', 'Buffers')])}
    
            

#menus = {'c07f2077d62ebfc8bcac419f134636b8abb7ffdd': 'Averaging',
#         '49ae92a0ba80a7290de84d7b59eaf4b580204018': 'Analysis',
#         '1c4ca7c5897bf8ff5c06730a3ba4f9fe5a367230': 'System RAM',
#         '5dba64a625981ad7543212266b123021de5fc9bb': 'Edit Limits',
#         'a6b1b7bf0059412dba334c711ea86f6b1eef9a7c': 'System',
#         '11d6b43ce5cc3ade98dec8e279be35d256d89ab9': 'Marker Statistics',
#         '4cc88429816f534d82f4a8a412654af32509f9d6': 'Storage',
#         'c6a464f3bee47a9d9a58390b15bbebcab5d3b865': 'Buffers',
#         '6baa4ce12d589ca4e8886cb50f48fa35dd244daf': 'Arb. Src. Settings',
#         '24fa1e61278232ce2b7a0115fe109503cf835ff2': 'Memory Allocation',
#         'bbeb6f78920082728ac3b7677cc9e2640bcc62a7': 'Transducer Units',
#         'b8e55efd6b4225e96f9e5876f6e4733d09b62a48': 'Input',
#         '384fe1216ea5b0804bd28b07fb4b4a0a0205f632': 'User Math',
#         'f37b6396133c7dcdc07564b95865a446d226dbcb': 'Disk Upkeep',
#         'c18071ba176a0b8091576c296790a8b347a1cb64': 'Input Con\xef\xac\x81g',
#         'c5a83efa0a1a70a067fe9801fe73795aad1720fa': 'Time',
#         'bb95f9a49d6c2989b62a336649c537f770e32254': 'Fit setup',
#         '0a7f1e2a2685e9327762072cd6aea1fd6e574ed5': 'Limit Testing',
#         '49554de55a66e26746029e8a4d63a7703a3d3d05': 'Data Table', 
#         'a31e9509b6ff7ce11a1aa7ffc232cdf8964797c7': 'Waterfall',
#         '71db1b47afe2f94a44a1937f0fb5fb6e3928b45b': 'Hardcopy Colors',
#         '590d8f294cb00f4da5b461b225e40fa36b6e8769': 'Test',
#         '3600290010aef50c267717a32b7ad2f8d35f574b': 'Memory Tests',
#         'b623105103231509183bc7f40328d24abfe03b37': 'Remote',
#         '4002f79646496fb0ebaae79cd780e2a598a9d035': 'Playback Con\xef\xac\x81g',
#         'aa50e561439bfe6a1a945909fc03292ba980464e': 'Frequency',
#         'e519c275816cacbfc495ee860d6d4f36794cd0be': 'Tone 2',
#         '558c5fd0bccf94a33780b253515a71bb74971e4c': 'Hardcopy Output',
#         '74ae44dc6b0fcec31397ca872dcbd3b0083b2bc4': 'Capture',
#         '68db1e9ed77650346edf1f1e4890373e712f6ce6': 'Get Settings', 
#         'af864451ff2a94647ffe4013bea66b4efc4ad103': 'Display Setup',
#         '7223408bae3d389c2d431e7368508a6dadfadf0f': 'More Options',
#         '1ea6b787e24c6659146fb03ff3afc71ba6dc3177': 'Window',
#         '9aeb67e273b3211c069170c8014c7c6b68899e75': 'Marker Setup',
#         'a855974c9ba95cc4067b31185df7a10102e1b0e1': 'Curve Fit',
#         '90db1a7766cb2521938408b93ea2eae6b9a6a452': 'P references',
#         'e6c4bec9cb4af088a366a1d27990823d4e74b588': 'Trigger',
#         '7433c1a55a468f1df1ecf37d6fc538e8cc23f579': 'Exceedance', 
#         'df8f38bc656f09d2424624c57cee78daef512f83': 'Source',
#         '297e4836b602585ecc86092e6909a57f9f470937': 'RPMfTime Arm'}
