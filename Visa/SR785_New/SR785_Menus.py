# -*- coding: utf-8 -*-
"""
Created on Thu Jan 07 16:46:49 2016

@author: wisp10
"""
BUTTON  = 1
SUBMENU = 2
TOGGLE  = 3
RETURN  = 4
ONOFF   = 5
ENUM    = 6
INT     = 7
FLOAT   = 8

menus = \
[   [   [33],
        'Frequency',
        'aa50e561439bfe6a1a945909fc03292ba980464e',
        [   (0, '5dc94ea82af6d49af6e9ae9f4d3b3d209b51b38c', None, None, 'Span'),
            (1, '57e68c95753f03a7b20f28477ae0252cb91f994f', None, None, 'Line Width'),
            (2, 'd12dd00569042fcc5988a14d0ac0cd1e491f8799', None, None, 'Acquisition Time'),
            (3, '476de5cb278b5a9520d4486f2867a19eee554bce', None, 'ButtonUnchecked', 'Full Span'),
            (4, '7a2e6e4b56b34d2c86ca34c71dfb9d9885c82445', None, None, 'FFT Lines'),
            (5, 'fd5c64056007bb387a252dc3fa1179765e078b1a', None, None, 'Base Freq.'),
            (6, 'b2f5e4e4e9adda86e435cd5edbc1ae38aad8f4a8', None, None, 'Start Freq.'),
            (7, 'b09e6d98c76f5288f34dfe344259be13c90a04e8', None, None, 'Center Freq.'),
            (8, '2d66268b10580ab98143f0cbc9a46be8d626bcb5', None, None, 'End Freq.'),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        []],
    [   [34],
        'Display Setup',
        'af864451ff2a94647ffe4013bea66b4efc4ad103',
        [   (0, 'a792bc9493c10d66c2e72bf0664d7a2bf901b583', None, None, 'Measure Group'),
            (1, '9d84f6fe06d97d6c1e1676b4afa891f8439646c6', None, None, 'Measurement'),
            (2, '0e2e4cf74b14ae8719eefa28cbdcdc8e0f8749a6', None, None, '\\\xef\xac\x81ew'),
            (3, '28744eb70503c4f665c37655d24d68236f1c18eb', None, 'SubMenu', 'Units'),
            (4, 'c37ebac0fb726f33c76bcf23b1278a54e7655d35', None, None, 'Ymax'),
            (5, '4feaed32ba9af946225fbf13d55748647b8f4fff', None, None, 'Ymid'),
            (6, '2a9de94f44693021d5e4c6cabc5d09a942375619', None, None, 'Ymin'),
            (7, '3b3ae028836f64e00769b199b2c638f617c3c102', None, None, 'YIDiv'),
            (8, '6b115fda8c24cac0c863a26dde7f2bfa4c41e2e0', None, None, 'Wm'),
            (9, 'fb25e2d8fb0c1ae0fc74de2559fdcbe39fcf3540', None, None, '')],
        [   [   [34, 10],
                'Units',
                '07034f881caf4ac35fea9dd39ae8f823c67fbafb',
                [   (0, '28744eb70503c4f665c37655d24d68236f1c18eb', None, None, 'Units'),
                    (1, 'a93a5abbbcae0d52d87d07b7fbaa08609f80fd9a', None, None, 'dB Units'),
                    (2, '62b297542e11a1728c9162a34e0b1635eec63635', None, None, 'P k. Units'),
                    (3, 'af6fce46af53a32bd6df8e7ee2798a8131fe8aba', None, None, 'P SD Units'),
                    (4, '4153452ac6bc0e2727de43bf8acf4865d61a9592', None, None, 'P hase Units'),
                    (5, 'e96a41c71e5acf9ca1dadf782725ba18f78f0a76', None, None, 'dBm Ref. Imped.'),
                    (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [35],
        'Display Options',
        '5c9751296e1d6046fa28411b41b0d105c3bc17c0',
        [   (0, 'bd985d3c555260b07f8f9eb6374e24ca9e61348f', None, None, 'Di5P|\xef\xac\x82Y'),
            (1, '72115a74f929300c0d01744934b9132eae912269', None, None, 'Format'),
            (2, 'f3c4e717055e798c1b8b4da9d4679b749a05d14c', None, None, 'X-Axis'),
            (3, 'cef5436301b6f5ad5977f839a72f4625d4946afc', None, None, 'RPM frequency'),
            (4, '7631c8fe29b6c4351a42151cd0209074327d1d61', None, None, 'Grid'),
            (5, '49a51a8bf8b095fc9c23cc0a74b44cafaa4d67b1', None, None, 'Grid Div'),
            (6, 'f5b8072aed84fc5a00dbdfd3e3430945a2c81b72', None, None, 'mmmw HM'),
            (7, '145c4831b6310dc129e20b46d3a4bcf494ebb7fe', None, None, 'Phase Suppress'),
            (8, 'c02a414cbf0c9fe7fe85a4716e46e94bd25f5ff8', None, None, 'dldx window 0%)'),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        []],
    [   [36],
        'Marker Setup',
        '9aeb67e273b3211c069170c8014c7c6b68899e75',
        [   (0, '1315680350a4816239f5e69d8a935c89ab6492c9', None, None, 'Marker'),
            (1, '9eeb5df006034ac9e5a907bbf6231baab6294593', None, None, 'Mode'),
            (2, '110e99e2bf876276a20fdf4ca2c3ca795e7d7ce2', None, None, 'Seeks'),
            (3, 'a539d7bb5365402873e624c8e3ecdcde07e452d7', None, None, 'Width'),
            (4, 'adae04ad9e66264f30f23c406be887d20c38649c', None, None, 'Rel'),
            (5, 'bd2d10c75452ec1d8b4d82c4e0a3ddcfd5fffe96', None, None, 'X-Rel'),
            (6, 'b6bb4f0a02aa26e97405b1109c9003cbcbfd9540', None, None, 'Y-Rel'),
            (7, 'bd2d10c75452ec1d8b4d82c4e0a3ddcfd5fffe96', None, None, 'X-Rel'),
            (8, 'e2c70e523af92a066efb5ef476c73b8c97ceca70', None, 'ButtonUnchecked', 'Marker X to'),
            (9, 'f05f70dd32704d5d1e652a7571704a5e68114d07', None, None, 'E\xef\xac\x82i\xc3\xa9j')],
        []],
    [   [41],
        'Source',
        'df8f38bc656f09d2424624c57cee78daef512f83',
        [   (0, 'c8214a264300bb871396fd3bd6fe4ff2870e6c08', None, None, 'Off'),
            (1, 'cbb869731c40bb8778f76671dec15894165d422a', None, None, 'On'),
            (2, '5005d94cd17aa559251e05438b70a07cd6310733', None, None, 'Sine'),
            (3, 'c8277909aef6bfa14d3403ab1aca49b192db33bf', None, None, 'chirp'),
            (4, 'cc10b1d0bf9de047e66e061a659ad0df95f9521c', None, None, 'Noise'),
            (5, 'cb027a5e2d627c5e8adb7cf708925200eddb8d6d', None, None, 'Arb'),
            (6, 'eea6b7b88466e1c65663b3af30543274f1f872f3', None, None, 'Amplitude'),
            (7, '00c764681f98b18cb8bf1fdfab71517e7c4693f5', None, None, 'Source Play Rate'),
            (8, 'ee8b1b5a9738c63ecb5ce4672d14ea470854e489', None, None, 'Source'),
            (9, '7c1eef631daaa8dd1a0af040423d3c50a087cb50', None, None, 'More')],
        []],
    [   [42],
        'Input',
        'b8e55efd6b4225e96f9e5876f6e4733d09b62a48',
        [   (0, '14f7668e22d2b122d79e7ae0ca5affb4580b1c82', None, None, 'Input Source'),
            (1, 'd97816f4db66abaf52ae557639179723d2c57c6f', None, None, 'Analyzer Con\xef\xac\x81g'),
            (2, 'cdc1fdda49d3d479643570d9e6a7478edcf86a60', None, 'SubMenu', 'Input Con\xef\xac\x81g'),
            (3, '286868a4435efd582ea626dfe1139105ad139b23', None, 'SubMenu', 'Trnsdcr P arams.'),
            (4, '9ebc49d5d1f8ac18c0c108011e456dca63b45999', None, 'SubMenu', 'Tach Input'),
            (5, '33372e77346c857a3fba2730ce54d22b7d7519b3', None, 'SubMenu', 'Playback Con\xef\xac\x81g'),
            (6, 'e4ccc30dd9ed80437213793c625e1492cfa761cf', None, None, 'Auto Offset'),
            (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        [   [   [42, 11],
                'Input Con\xef\xac\x81g',
                'c18071ba176a0b8091576c296790a8b347a1cb64',
                [   (0, 'f0f03be608edb8a46b6707ffeca9a4ffbe25d89b', None, None, 'Channel'),
                    (1, '3d70372d4fde860b8baa74332d9bc1de432b9826', None, None, 'CH1 Input Mode'),
                    (2, 'bbbc78bad57ef48a77bcbef88f9be3b1334c1072', None, None, 'cm Grounding'),
                    (3, '44ce8e416b5cc207f51fa92a4d793940bff07875', None, None, 'CH1 CoLIP|irI9'),
                    (4, 'c58d9bd544adf4cfefc3995fb93252b024ce3212', None, None, 'cm Input Range'),
                    (5, '5b4ae45f84c091778dbc34bc897dc2a9c687587f', None, None, 'CH1 AA Filter'),
                    (6, 'e96c0ac642d4e7f1fa5a4afba6f18baad3cc0f56', None, None, 'CH1 A-Wt Filter'),
                    (7, '2b704af495df410e9cf33d8d9c6f140813638338', None, None, 'cm AutoRange'),
                    (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', None, 'Return'),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [42, 10],
                'Transducer Units',
                'bbeb6f78920082728ac3b7677cc9e2640bcc62a7',
                [   (0, 'f0f03be608edb8a46b6707ffeca9a4ffbe25d89b', None, None, 'Channel'),
                    (1, '66d5453cc9fa52b8fb84595e60ff0d86e3744e6a', None, None, 'CH1 Eng. Units'),
                    (2, 'd1a32a30f3a252a618ee8c28fafefbecfa279c77', None, None, 'CH1 EU Label'),
                    (3, '39a4bc4b487688e2a51b679b70bfa6a29cecc026', None, None, 'CH1 EU IVo|t'),
                    (4, '5ebbbe1d5110ecddf21c7ee1dfc464365da31182', None, 'ButtonUnchecked', 'MM 1 Hm! mum'),
                    (5, '18f15e5bbe1f723b786b353dea3e072c700cac75', None, None, 'CH1 User Label'),
                    (6, '3cb91a39b667fe608c97e24db2a20262f23f70b2', None, None, 'mmm'),
                    (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [42, 9],
                'Tach Input',
                '640e28ad6d4eeb0dab259c9d2c7fe9ad9310a65c',
                [   (0, '3e310d949cce1f04273f79f65c657df984342466', None, None, 'Pulses per Rev'),
                    (1, '3e3f396ca9a05d2b3128f89c46bea6340ddbd40d', None, None, 'Tach Trig Rng'),
                    (2, '5586b499807ba19563d991065a3086e4569df4f1', None, None, 'M\xe2\x80\x98!'),
                    (3, '2bb6abc5be03662bc0c3ef0be5504eb97d41e8ab', None, None, 'Tach Slope'),
                    (4, 'a0641df467f9839558541c3c0bfe44a697b19e7f', None, None, 'Hold Off Enable'),
                    (5, '81ae40b239c6d1e567d2c8e9cb2285660bd42e00', None, None, 'Tach Hold Off'),
                    (6, '651bcb79d9f3fa8ac89bd7ecda547ab2f11563f1', None, None, 'Show Tach'),
                    (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [42, 8],
                'Playback Con\xef\xac\x81g',
                '4002f79646496fb0ebaae79cd780e2a598a9d035',
                [   (0, '36182ee616e07c5cd26f740969b5507477faffea', None, None, 'Playback Start Pt.'),
                    (1, '60aee4d5ab7dd8f69f1fe2942cf4db108bb8d255', None, None, ''),
                    (2, 'b59d374b7ef9f50ab45a7c6d77ea1df5cfe6198d', None, None, 'Playback Length'),
                    (3, '60aee4d5ab7dd8f69f1fe2942cf4db108bb8d255', None, None, ''),
                    (4, 'f2b119ada974fa25b965dabc1563686d23892c44', None, 'ButtonUnchecked', 'm 1 M! 1 Mm'),
                    (5, 'ff1971535ab7e5b1d4761abf24e0e2058408f383', None, 'ButtonUnchecked', 'm\xe2\x80\x98! LMMH \xe2\x80\x98'),
                    (6, 'bd7d62bf27e327d541539dccfa31c38bb5b3b24b', None, None, 'Playback Mode'),
                    (7, '5bd1358384714a6ed40ba71ab9b7f1bb3ba182d6', None, None, 'Playback Speed'),
                    (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [43],
        'Trigger',
        'e6c4bec9cb4af088a366a1d27990823d4e74b588',
        [   (0, '6ceb07925ab9566c5a766f282bcbf9120c64ddbf', None, None, 'Trigger Mode'),
            (1, '74b8d2550c33d15024716fefdfa3b1fd7dfa3fd0', None, None, 'Trigger Source'),
            (2, '7162ed32757ca4b3b43358bbee6793918526575a', None, None, 'MM J'),
            (3, '2f7106dbac0ad5d1a0512c51b1be0e8401f8cb14', None, None, '\xe2\x80\x98Hum Mwmw'),
            (4, 'f9c7d001f328274bf1920a274d431b496e94737c', None, None, 'Delay A'),
            (5, 'f5a57903da5142044f15e72095168cb83d635340', None, None, 'Delay 5'),
            (6, '96d54ca700ab221b4f2bfcdf7c26b2f7656bfe13', None, None, 'Vmmmw Hmh\xe2\x80\x98'),
            (7, '77e1bc67a28dab39022097f40027c0c4ee7e74d5', None, 'SubMenu', 'RPMfTime Setup'),
            (8, '1f7525d3a88c09a639694297674779bf8e74edc2', None, 'ButtonUnchecked', 'Manual Arm'),
            (9, 'aece5946f911714d4475dedeed505850de3903f3', None, 'ButtonUnchecked', 'Manual Trigger')],
        [   [   [43, 24],
                'RPMfTime Arm',
                '297e4836b602585ecc86092e6909a57f9f470937',
                [   (0, '78254f2a6459f6dbce5067d04edb5b97ced45b16', None, None, '\xc2\xabmm L'),
                    (1, '78254f2a6459f6dbce5067d04edb5b97ced45b16', None, None, '\xc2\xabmm L'),
                    (2, 'f671377997bf97e124e05c6d1ce0b2df443d99c4', None, None, 'Delta RPM'),
                    (3, '9182710564f21f6fb84952af37965c9576d58c91', None, None, 'Delta RPM Sense'),
                    (4, '9489da03dcf9e19796cc1e4ebe9aeb6043fb0ed4', None, None, 'Time Arm Step'),
                    (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [44],
        'Averaging',
        'c07f2077d62ebfc8bcac419f134636b8abb7ffdd',
        [   (0, 'a04de0b8c937db1ed7b403d68aa2ba1830e5e1c4', None, None, 'Compute Avgs'),
            (1, 'd39b7eaaf15cb89c5f2220a8b8848524337f0f6a', None, None, 'Averaging TYP9'),
            (2, '8ce43c38d3f437f4944ebc18041328f5271143d2', None, None, 'it Avgs'),
            (3, 'c1c1ff117453fdcb0fc2cf7ce8609df057e53ce7', None, None, 'Display Avg'),
            (4, '7cdf882173128f98b13f4e18886bd224dd9a7692', None, None, 'Time Record Incr.'),
            (5, '7c1eef631daaa8dd1a0af040423d3c50a087cb50', None, 'SubMenu', 'More'),
            (6, 'ab853e1c4fa12bb43353748128d00d5fb50bed42', None, None, '\xe2\x80\x9cU Wm \xe2\x80\x98H \xe2\x80\x9c'),
            (7, 'fdcfc093d7cf72a80c6e0e8490461f9c4033790d', None, None, '\xe2\x80\x9c um'),
            (8, 'f3783e020d185fbc77e4974b2c9f0f2c82e73e37', None, 'ButtonUnchecked', 'm w w w'),
            (9, '585326ca5d8eed890a5b6ea51af1d2b709cf391f', None, None, 'V\xe2\x80\x98')],
        [   [   [44, 8],
                'More Options',
                '7223408bae3d389c2d431e7368508a6dadfadf0f',
                [   (0, '3d2f8959fc1bac9378afa52dcdf1c0f49488ade6', None, None, 'Overload Reject'),
                    (1, 'be142660fa7145962ea04826af2862be088eb7f6', None, None, 'Trigger Avg. Mode'),
                    (2, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (3, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (4, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (5, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [49],
        'User Math',
        '384fe1216ea5b0804bd28b07fb4b4a0a0205f632',
        [   (0, 'f364cd917a5805d34bc3e5cc1d5c3625e67ee55e', None, None, 'Function:'),
            (1, '557fd25ae1b36b615ca23667fdfbf0e18cdedbd4', None, 'SubMenu', 'Edit Fn.'),
            (2, '7c3e8ca1643ec65410da43398c66e092beaadd95', None, 'SubMenu', 'Edit Const'),
            (3, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (4, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (5, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        [   [   [49, 12],
                'Edit Function',
                '914771cecca5236c483ae21b1d59388911aa35a8',
                [   (0, 'e47d9f56bc6d549a2f3f1bb6e964f874d28deebf', None, 'ButtonUnchecked', 'Operands'),
                    (1, 'e956f7ec0fe33b5dde3c403c1fb97966fd5020e4', None, 'ButtonUnchecked', 'Operations'),
                    (2, 'c756589a095e6587bdd90440534e5cf61d92a6e7', None, 'ButtonUnchecked', 'Function String'),
                    (3, 'b0ea50dad5d2079d9bb440d5aa52cbb0ddac1d2e', None, 'ButtonUnchecked', '<|nsert IRep|ace>'),
                    (4, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (5, 'a95d33192d1622331c5573399dac474664ed339f', None, 'ButtonUnchecked', 'Delete'),
                    (6, '98dd5751b6a852abdb6f3f784a06c77a21c19003', None, 'ButtonUnchecked', 'Clear Eq.'),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '5966ee15eaa505a47ed4c14544cda4132cf72afa', None, 'ButtonUnchecked', 'Cancel'),
                    (9, 'f206a50c630c984e37e5398dd8f4a216bc86a2c5', None, 'ButtonUnchecked', 'Enter Eq.')],
                []],
            [   [49, 11],
                'Edit Const',
                'bb39660098d2dec78e2473662184415c6d9d5644',
                [   (0, 'd15a2808a33de19576ac134a2e5efa69a5a39c1d', None, None, 'Constant'),
                    (1, '67ae035c22ae830207462fa7007a138020ca989d', None, None, 'Real P art'),
                    (2, '1cba5fbf0d20fd65e98582b4bfa80eb9f86d98f4', None, None, 'Imag P art'),
                    (3, 'a38a03c7778ccefca1f460dc605a9f99193c3c09', None, None, 'Mag'),
                    (4, '3f9fce994b204180a3684c781b83a34ed5c31e16', None, None, 'Phase ((199)'),
                    (5, '616860e1f1524f37657afafaafa2955eabf09505', None, 'ButtonUnchecked', 'Marker->Mag'),
                    (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [50],
        'Window',
        '1ea6b787e24c6659146fb03ff3afc71ba6dc3177',
        [   (0, '02f89bd0314dc968a9fc3eeef4e6f0b206e05f06', None, None, 'Window'),
            (1, '20ad3a369434b4fb05d056d003c9fa8da7ea5f0e', None, None, 'mm \xe2\x80\x9c \xe2\x80\x9c um \xe2\x80\x98WV!'),
            (2, '2fd48b1f2242b8bb9a1bb7d1f920164e42e3cbc5', None, None, 'mm M um \xe2\x80\x98WV!'),
            (3, '3da0f300c1a9e0fa0eeae62fb6bd58adac972add', None, None, 'Mm 1 Huh'),
            (4, '121ef4b8f844bb524d21e1561a74f67339adb7b0', None, None, 'Mm H;'),
            (5, '60aee4d5ab7dd8f69f1fe2942cf4db108bb8d255', None, None, ''),
            (6, '3f97aee010f26e3f38fd0d53eb9ce6330a994900', None, 'ButtonUnchecked', 'Trace to Window'),
            (7, '1ddd4587fc67c8e60121bfc074907c861b6115e2', None, 'ButtonUnchecked', 'Window (0 Trace'),
            (8, 'ef805acd109fca4185c49f42a234e3c533e723dc', None, None, 'um \xe2\x80\x98VVV\xe2\x80\x98 mm'),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        []],
    [   [51],
        'Waterfall',
        'a31e9509b6ff7ce11a1aa7ffc232cdf8964797c7',
        [   (0, 'bd985d3c555260b07f8f9eb6374e24ca9e61348f', None, None, 'Di5P|\xef\xac\x82Y'),
            (1, 'a65eca025a317a19a9b6911bce9d7831ac7dac55', None, None, 'Storage'),
            (2, '62d7c6adfaf50a35e71a107fae0412d46c65fbd7', None, None, 'Save Option'),
            (3, '17369f42313855cb4b762285ff87dfaa1f4b587a', None, None, 'Total Count'),
            (4, 'eb7914cb88cd5cac3aad2214a64e5a712cbfbcba', None, None, 'Ski!\xe2\x80\x99'),
            (5, 'd4f4751383f8a170e3901ed34311ad05ea231c0f', None, None, '\\\xef\xac\x81ew Count'),
            (6, 'd6f5312096fb97b13dde8e71d0bc09a5f4b46158', None, None, 'Angle'),
            (7, 'a5b6bc9ca2c12c35ce1df99b346e011a09fb6ef7', None, None, 'Marker Z to'),
            (8, 'fdceaf9c9fb4ded1567b106e913adde64a55f06c', None, 'SubMenu', 'Allocate Mem.'),
            (9, '021a1edbcd8dca8aa26200b40c1eea8e31d60c72', None, 'SubMenu', 'More...')],
        [   [   [51, 32],
                'Memory Allocation',
                '24fa1e61278232ce2b7a0115fe109503cf835ff2',
                [   (0, '1b96497d53483551bccb325ae0eea737bd038857', None, None, 'Total Available'),
                    (1, '251fd717ce96e229d8af58087b3051473d36f9aa', None, None, 'Capture'),
                    (2, '51c8e8ab2c24f06808c3bfe6d70ff2ddc9c044b0', None, None, 'Waterfall I Order'),
                    (3, '4c3ce4e6ac8018cef03680143fe596d08d06d1e9', None, None, 'Arb. Source'),
                    (4, '94f5f1702d19853f3acb0a04e649534f33e4160e', None, 'ButtonUnchecked', 'Con\xef\xac\x81rm Allocation'),
                    (5, '2a926b3594f9b807619b49b461a31442a3f8042f', None, 'ButtonUnchecked', 'Clear Allocation'),
                    (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [51, 40],
                'Waterfall',
                'a31e9509b6ff7ce11a1aa7ffc232cdf8964797c7',
                [   (0, 'd61890ea00c5b3d1c45b6b5fb18b1abaa8affb5a', None, None, 'Trace Height'),
                    (1, '9db1650a6ccc9826a266df499790a8e2ab597046', None, None, 'Fast Angles'),
                    (2, 'c7a3c466478821e3407657b00ad76a4da06f5130', None, None, 'Threshold'),
                    (3, 'ae6c72fb38b0b15a0b0bd82aa06ffac66bdddb6d', None, None, 'Hidden Lines'),
                    (4, 'cd075b12d046b85d4b52bba4bc613ea4bd2ef00c', None, None, 'Paused Drawing'),
                    (5, '549a634e87638d1b1777e073b31c14c844f5d8cb', None, 'ButtonUnchecked', 'Record (0 Trace'),
                    (6, '6a877ada6e25896f9132ce9a4eab11a5ce0f0671', None, 'ButtonUnchecked', 'Slice (0 Trace'),
                    (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [52],
        'Capture',
        '74ae44dc6b0fcec31397ca872dcbd3b0083b2bc4',
        [   (0, '805a798fe5443f7163d917f657af88ca488e8560', None, None, 'Capture Channels'),
            (1, '779ac449bb9eb0065596d588f103795165b425c1', None, None, 'Capture Mode'),
            (2, '0de4fdf3dc12c2da4cd32a8c98a5ed6a82196c9c', None, None, 'Capture Length'),
            (3, '60aee4d5ab7dd8f69f1fe2942cf4db108bb8d255', None, None, ''),
            (4, 'eb349814d94d48ba4c1879c592d5066d45527785', None, None, 'Sampling Rate'),
            (5, 'fdceaf9c9fb4ded1567b106e913adde64a55f06c', None, 'SubMenu', 'Allocate Mem.'),
            (6, 'aaa675a8e7836caa266cecda80a6cc2967ed35e8', None, 'ButtonUnchecked', '\\\xef\xac\x81ew Header'),
            (7, '630c1862379fd40b2a7e87470d35b03fc374f3e1', None, None, 'Auto Pan'),
            (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        [   [   [52, 8],
                'Memory Allocation',
                '24fa1e61278232ce2b7a0115fe109503cf835ff2',
                [   (0, '1b96497d53483551bccb325ae0eea737bd038857', None, None, 'Total Available'),
                    (1, '251fd717ce96e229d8af58087b3051473d36f9aa', None, None, 'Capture'),
                    (2, '51c8e8ab2c24f06808c3bfe6d70ff2ddc9c044b0', None, None, 'Waterfall I Order'),
                    (3, '4c3ce4e6ac8018cef03680143fe596d08d06d1e9', None, None, 'Arb. Source'),
                    (4, '94f5f1702d19853f3acb0a04e649534f33e4160e', None, 'ButtonUnchecked', 'Con\xef\xac\x81rm Allocation'),
                    (5, '2a926b3594f9b807619b49b461a31442a3f8042f', None, 'ButtonUnchecked', 'Clear Allocation'),
                    (6, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [57],
        'Analysis',
        '49ae92a0ba80a7290de84d7b59eaf4b580204018',
        [   (0, '444aeb605294dec439d947f7906afd4d50809316', None, 'SubMenu', 'Data Table'),
            (1, 'ddbb2a1f19b6b9ae8ca2fd6a3fe7e8b48627da33', None, 'SubMenu', 'Limit Test'),
            (2, 'bcd7ba0f1c44b8bec89375aba0639f63e1dfd060', None, 'SubMenu', 'Marker Stats.'),
            (3, '00bcd9d221fb9b7718d47597c4ed396826ebb057', None, 'SubMenu', 'Exceedance Stats.'),
            (4, '98efffeff072ed245ea4910f32ad0bd263a673f2', None, 'SubMenu', 'Curve Fit'),
            (5, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
        [   [   [57, 0],
                'Data Table',
                '49554de55a66e26746029e8a4d63a7703a3d3d05',
                [   (0, '444aeb605294dec439d947f7906afd4d50809316', None, None, 'Data Table'),
                    (1, 'ae0231c12c3c9884de99da68e83157fcaf692254', None, 'ButtonUnchecked', 'Insert Line'),
                    (2, '923a07024aa8aeddef35960d4356d7e9bfe5b28d', None, 'ButtonUnchecked', 'Modify Line'),
                    (3, 'd8f7ef7285abb4d64298ce32110d601811c31565', None, 'ButtonUnchecked', 'Delete Line'),
                    (4, '4d55e1e24ea09eda252fb335e932d6070d60484a', None, 'ButtonUnchecked', 'Clear Table'),
                    (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [57, 12],
                'Limit Testing',
                '0a7f1e2a2685e9327762072cd6aea1fd6e574ed5',
                [   (0, '4d24aeab5387956e84f5e0357483a7d28974d8ed', None, None, 'Limit Segments'),
                    (1, 'a211d83af55534f33e45de0194fdb2b2d0786b72', None, None, 'Limit Testing'),
                    (2, '974615385e40bb8615b7c42c07a4a36417fb800b', None, None, 'Limit BeeP'),
                    (3, '5e50dcf3351254a59950e5e7ec4d702fdf81216f', None, 'ButtonUnchecked', 'Clear Limits'),
                    (4, '71e0cddfb494adad07192d303159c38a3a402342', None, 'SubMenu', 'Edit Limits'),
                    (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                [   [   [57, 12, 9],
                        'Edit Limits',
                        '5dba64a625981ad7543212266b123021de5fc9bb',
                        [   (0, 'c9d1ed8877bcd79fa1b446a089bbbac5424315fc', None, 'ButtonUnchecked', 'New Segment'),
                            (1, '18dd6f2b93bbe1a7b4aadd81cb099ef84e8b6add', None, None, 'Limit Type'),
                            (2, 'dc8d4001b708a73030d92302acbccb84ad64a2a2', None, None, 'Segment it'),
                            (3, '4940070e56fb318c3369cdd1cf043f10dd9c2414', None, None, 'X0'),
                            (4, '8dcba6c3badb2ca6269606e98ab2994160858830', None, None, 'Y0'),
                            (5, '0fdb847db6c146f7ed3b60ec8f71d49823a93fba', None, None, 'X1'),
                            (6, '739c89e58720cbad5e1ef8329e764caecb949c65', None, None, 'Y1'),
                            (7, 'a46618a8540c2dde313a47525a88c593857143f0', None, 'ButtonUnchecked', 'Delete Segment'),
                            (8, '84d17ad2bb1d773fff3fff0391305ee96e273901', None, None, 'Shift All'),
                            (9, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return')],
                        []]]],
            [   [57, 11],
                'Marker Statistics',
                '11d6b43ce5cc3ade98dec8e279be35d256d89ab9',
                [   (0, 'bcd7ba0f1c44b8bec89375aba0639f63e1dfd060', None, None, 'Marker Stats.'),
                    (1, 'f25b0564c523624917459e8f4929a2d2b2d785db', None, 'ButtonUnchecked', 'Reset'),
                    (2, '92c8c58e1a07b63fceb4e389f7c420c5c3621736', None, None, 'Max (Display A)'),
                    (3, 'da49a7b4f968012b88de05192fe5b785fea984d1', None, None, 'Min'),
                    (4, 'eac17700b5364022bdf41bf31ee75141a1214547', None, None, 'Mean'),
                    (5, '3f8c2dced1fd975b11e573ce6ba2783c60a149c4', None, None, 'Std. Dev.'),
                    (6, '58dfafbc6049bf17a6fafa198e6cbf07a3765793', None, None, 'Max (Display B)'),
                    (7, 'da49a7b4f968012b88de05192fe5b785fea984d1', None, None, 'Min'),
                    (8, 'eac17700b5364022bdf41bf31ee75141a1214547', None, None, 'Mean'),
                    (9, 'f2efaffef01278c94d0e37e13f33413efaedea07', None, None, '..r')],
                []],
            [   [57, 10],
                'Exceedance',
                '7433c1a55a468f1df1ecf37d6fc538e8cc23f579',
                [   (0, '31ef8c924f584048582e1df6d15ca0b0acabfc79', None, None, 'Start Index'),
                    (1, '9908bbbed4f2499bb985312f154de0116a817ff4', None, None, 'Stop Index'),
                    (2, '645888f3637c36304368c426cf0e155a56eb9dd3', None, None, 'Exceedance Pct.'),
                    (3, 'd84d9e17cd6c94d60664d0437e9acc7b1c500cc6', None, 'ButtonUnchecked', 'Calculate Excd.'),
                    (4, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (5, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []],
            [   [57, 9],
                'Curve Fit',
                'a855974c9ba95cc4067b31185df7a10102e1b0e1',
                [   (0, 'b84c9c0d197878faf4c1732a6063f3cdd2842df5', None, 'ButtonUnchecked', 'Start Fit'),
                    (1, '690f8088b3570b8cb921be41ea6cad511c30a7b4', None, 'ButtonUnchecked', 'Abort Fit'),
                    (2, '1767cffcd6031dbcf4ee19e1fc1bd8f8f6ae87ca', None, 'ButtonUnchecked', 'Synthesile Tb|.1'),
                    (3, '76118df8b5bb8e121131c11d308f59b656274e3b', None, 'ButtonUnchecked', 'Synthesile Tb|.2'),
                    (4, '7c885a9000948151f3f376859a666c2d63c594eb', None, 'SubMenu', 'Fit setup'),
                    (5, 'bf369074f8baaad1cea0c9e0e3f3ca1a263cd8c2', None, None, 'Table'),
                    (6, 'fbf8fb321673d3a0d9ebeb260edff6c1b27c7178', None, 'SubMenu', 'mu mm'),
                    (7, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                [   [   [57, 9, 9],
                        'Fit setup',
                        'bb95f9a49d6c2989b62a336649c537f770e32254',
                        [   (0, '4015498587794bbf3cb28f3c52d8ffb0af45395b', None, None, 'Number Poles'),
                            (1, 'c0a3c2fe7f3b949c8c5915a0ce52cbfdbf4142db', None, None, 'Number Zeros'),
                            (2, 'e515c262c3783f6d8bd95506808ebebce678ca27', None, None, 'Weighting'),
                            (3, '874405d1134492c1029c8bdb9e1c433a96dba686', None, None, 'Weighting Trace'),
                            (4, '754158687e4d7d976c6592f98e4b89bd9c2ddaef', None, 'ButtonUnchecked', 'Set Fit Rgn'),
                            (5, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                            (6, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                            (7, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                            (8, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, ''),
                            (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                        []]]]]],
    [   [58],
        'Storage',
        '4cc88429816f534d82f4a8a412654af32509f9d6',
        [   (0, 'f9600280cc5fa064bc8cfc8b25c1f286b44697ce', None, None, 'File Name'),
            (1, '3a8d8a59551125177b2bb1512b7eeda6d8f02652', None, None, 'Current Directory'),
            (2, '78782e0feacc0f54c58b06475002e6de996f44f3', None, 'ButtonUnchecked', 'Display to Disk'),
            (3, 'c43af6f9870e6928377f87e23e023ea5e69e090f', None, 'ButtonUnchecked', 'Disk (0 Display'),
            (4, '2e49480534dd10864061df161498555b7560d164', None, 'ButtonUnchecked', 'Settings (0 Disk'),
            (5, 'fdd5238b8696aeb12724c7f147cf2ece91e56251', None, 'SubMenu', 'Recall Settings'),
            (6, '36dd6a6bca7b6dc66b9be3a40240cbd4633a202a', None, 'ButtonUnchecked', 'Trace to Disk'),
            (7, 'cfb0e8e4f5fc4a0625cac94b7ce822d070d8152f', None, 'ButtonUnchecked', 'Disk (0 Trace'),
            (8, 'e21dbda7697bde2874df75dfcacaf7d1ac056a97', None, 'SubMenu', 'Buffers'),
            (9, '4c242a3b903ba5eb5ec6ce4bc70f0e068810b651', None, None, 'Disk Upkeep')],
        [   [   [58, 8],
                'Get Settings',
                '68db1e9ed77650346edf1f1e4890373e712f6ce6',
                [   (0, 'f9600280cc5fa064bc8cfc8b25c1f286b44697ce', None, None, 'File Name'),
                    (1, '3a8d8a59551125177b2bb1512b7eeda6d8f02652', None, None, 'Current Directory'),
                    (2, '34a47acae3f2887e8b7b63c84abc8c4f6d12599d', None, 'ButtonChecked', 'Measurements'),
                    (3, '77eac48e9cd225a008a58a486928b15e9073003d', None, 'ButtonChecked', 'Sources'),
                    (4, '74a7b4ac46886431c4c0be51f65b5428f2b4ffe5', None, 'ButtonChecked', 'Analysis'),
                    (5, '6a9099026c4b0ab4c8a866d37de84b420524f5f2', None, 'ButtonChecked', '|nputsfTriggers'),
                    (6, '732ba5ac276bf991b28759aff142595b6f9fa132', None, 'ButtonChecked', 'DRAM settings'),
                    (7, '8b7973aecff39402793b39fc774507e158c4b43a', None, 'ButtonChecked', 'Gen. System'),
                    (8, 'c9a7e055b4009c95ad5461c9bd4a7b3bbeb902ee', None, 'ButtonChecked', 'Macros'),
                    (9, '7db40dcbc455b42c7e36db9517d3953fd15de7fb', None, 'ButtonUnchecked', 'Recall from Disk')],
                []],
            [   [58, 32],
                'Buffers',
                'c6a464f3bee47a9d9a58390b15bbebcab5d3b865',
                [   (0, 'f9600280cc5fa064bc8cfc8b25c1f286b44697ce', None, None, 'File Name'),
                    (1, '3a8d8a59551125177b2bb1512b7eeda6d8f02652', None, None, 'Current Directory'),
                    (2, '1df0287e02e63a06417e6082a283c60d40d5c2a5', None, 'ButtonUnchecked', 'Ld Trc Data (Ascii)'),
                    (3, 'd583cb1648da5ccf71f7b0e94354584214453114', None, 'ButtonUnchecked', 'Ld Trc Data (Bin)'),
                    (4, '746b1d6e90a2ca19a452a59a130264fd1d534f43', None, None, 'Buffer'),
                    (5, 'b2928720f573e71fa0c1f41ee342f4a7e164ef2c', None, None, 'an'),
                    (6, '0136a9947b262f0ff724add245e387bbdc0b5a00', None, 'ButtonUnchecked', 'Disk (0 Buffer'),
                    (7, '7e705816c545214a8672064fdabcb7fbde18b19d', None, 'ButtonUnchecked', 'Mum M! m'),
                    (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]],
    [   [59],
        'Hardcopy Output',
        '558c5fd0bccf94a33780b253515a71bb74971e4c',
        [   (0, '9a97024784995a68f962d79e056135cc5bfaa09b', None, None, 'Hard copy Button'),
            (1, '8172f25770c5d37afc9efb96574173c832160801', None, None, 'Bitmap I P rinter'),
            (2, '41ca672b214d1d9e4703900f35ea654f39a8ba11', None, None, 'Bitmap area'),
            (3, '7060c10a4ecbb51975e051b4ad20e8f12d17ba24', None, None, 'Vector IP|otter'),
            (4, '206558b42a73ce0da198a077403cf1d6a9e24330', None, None, 'Destination'),
            (5, '2728e777757b703bc7fc539ff19be55a13e132fe', None, None, 'GPIB Control'),
            (6, '8c59b9e51a992ba0f76ed1d39f3a20d7ce433b44', None, None, 'H1 mhhmm'),
            (7, '3867b632f929de431460801c78c57e44b196cb79', None, 'ButtonUnchecked', 'Edit A Note'),
            (8, '995fbc684019a2aef5af8b8efa916e561a63b464', None, None, 'File Start Number'),
            (9, '38819d792603ef2495b6cfd52819b63bf32f91ca', None, 'SubMenu', 'Colors')],
        [   [   [59, 40],
                'Hardcopy Colors',
                '71db1b47afe2f94a44a1937f0fb5fb6e3928b45b',
                [   (0, 'c9ab5bb98de99b5dffce9d8690b74f0692d04530', None, None, 'Print Bright'),
                    (1, '826c5d28db2acb45374af634c69cf2a924fdda5d', None, None, 'Print Dim'),
                    (2, '3c03ef2676e0ef3888379718bd8dd94741d445d7', None, None, 'Print Black'),
                    (3, 'e212f53ab60a418a29da90eb6b007fa1f594655b', None, None, 'Print Graph'),
                    (4, '9830056cd8efa7a6b5715179345300fa884cde4f', None, None, 'Plotter Text Pen'),
                    (5, 'd262c3895dbaa4c38f125fe44a0fefb094be169d', None, None, 'Plotter Grid Pen'),
                    (6, 'bfc86a9ebb5a828a834fe92a89a4fead5304f49f', None, None, 'Plotter Trace Pen'),
                    (7, '29be9985c9dcc958be92c5b0b0c68044627cf0c5', None, None, 'Plotter Marker Pen'),
                    (8, '803eb2d5a78a1b4e8f07cb6f4cbc7600bbb0bcc1', 'Return', 'ButtonUnchecked', 'Return'),
                    (9, '4d8c0270cad6cd45dbe3afacaabb0ba830015f88', 'Black', None, '')],
                []]]]]
              