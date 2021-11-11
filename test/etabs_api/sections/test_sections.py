import pytest
import comtypes.client
from pathlib import Path
import sys

civil_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(civil_path))
from etabs_api import functions

@pytest.fixture
def shayesteh(edb="shayesteh.EDB"):
    try:
        etabs = etabs_obj.EtabsModel(backup=False)
        if etabs.success:
            filepath = Path(etabs.SapModel.GetModelFilename())
            if 'test.' in filepath.name:
                return etabs
            else:
                raise NameError
        else:
            raise FileNotFoundError
    except FileNotFoundError:
        helper = comtypes.client.CreateObject('ETABSv1.Helper') 
        helper = helper.QueryInterface(comtypes.gen.ETABSv1.cHelper)
        ETABSObject = helper.CreateObjectProgID("CSI.ETABS.API.ETABSObject")
        ETABSObject.ApplicationStart()
        SapModel = ETABSObject.SapModel
        SapModel.InitializeNewModel()
        SapModel.File.OpenFile(str(Path(__file__).parent / edb))
        asli_file_path = Path(SapModel.GetModelFilename())
        dir_path = asli_file_path.parent.absolute()
        test_file_path = dir_path / "test.EDB"
        SapModel.File.Save(str(test_file_path))
        etabs = functions.EtabsModel()
        return etabs

class Section:
    def __init__(self, d):
        self.name = f"IPE{d}"
        self.d_equivalentI = d
        self.bf_equivalentI = d / 2
        self.tf_equivalentI = d / 30
        self.tw_equivalentI = d / 40
        self.area = 1
        self.J = 1
        self.Ix = self.Iy = 1
        self.ASx = self.ASy = 1
        self.Sx = self.Sy = 1
        self.Zx = self.Zy = 1
        self.Rx = self.Ry = 1
        self.cw = 1
        self.xml = self.__str__() 

    @staticmethod
    def exportXml(fname, sections):
        fh = open(fname, 'w')
        fh.write('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<PROPERTY_FILE xmlns="http://www.csiberkeley.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.csiberkeley.com CSIExtendedSectionPropertyFile.xsd">\n'
                 '   <EbrahimRaeyat_Presents>\n'
                 '      <Comment_on_CopyRight> This database is provided by: EbrahimRaeyat, (2021); http://www.ebrahimraeyat.blog.ir </Comment_on_CopyRight>\n'
                 '   </EbrahimRaeyat_Presents>\n'
                 '  <CONTROL>\n'
                 '      <FILE_ID>CSI Frame Properties</FILE_ID>\n'
                 '      <VERSION>1</VERSION>\n'
                 '      <LENGTH_UNITS>mm</LENGTH_UNITS>\n'
                 '      <FORCE_UNITS>kgf</FORCE_UNITS>\n'
                 '  </CONTROL>\n\n')
        for section in sections:
            fh.write(section.xml)
        fh.write('\n</PROPERTY_FILE>')
        return True, "Exported section properties to "    # "%s" % (QFileInfo(fname).fileName())

    def __str__(self):
        secType = 'STEEL_I_SECTION'
        s = ('\n\n  <{}>\n'
             '\t<LABEL>{}</LABEL>\n'
             '\t<EDI_STD>{}</EDI_STD>\n'
             '\t<DESIGNATION>G</DESIGNATION>\n'
             '\t<D>{}</D>\n'
             '\t<BF>{}</BF>\n'
             '\t<TF>{}</TF>\n'
             '\t<TW>{}</TW>\n'
             '\t<FRAD>0</FRAD>\n'
             '\t<A>{:.0f}</A>\n'
             '\t<AS2>{:.0f}</AS2>\n'
             '\t<AS3>{:.0f}</AS3>\n'
             '\t<I33>{:.0f}</I33>\n'
             '\t<I22>{:.0f}</I22>\n'
             '\t<S33POS>{:.0f}</S33POS>\n'
             '\t<S33NEG>{:.0f}</S33NEG>\n'
             '\t<S22POS>{:.0f}</S22POS>\n'
             '\t<S22NEG>{:.0f}</S22NEG>\n'
             '\t<R33>{:.1f}</R33>\n'
             '\t<R22>{:.1f}</R22>\n'
             '\t<Z33>{:.0f}</Z33>\n'
             '\t<Z22>{:.0f}</Z22>\n'
             '\t<J>{:.0f}</J>\n'
             '\t<CW>{:.0f}</CW>\n'
             '  </{}>'
             ).format(secType, self.name, self.name, self.d_equivalentI, self.bf_equivalentI, self.tf_equivalentI,
                      self.tw_equivalentI, self.area, self.ASy, self.ASx, self.Ix, self.Iy,
                      self.Sx, self.Sx, self.Sy, self.Sy, self.Rx,
                      self.Ry, self.Zx, self.Zy, self.J, self.cw, secType)
        return s

def test_import_sections_to_etabs(shayesteh):
    sections = [Section(140), Section(160)]
    ret = shayesteh.sections.import_sections_to_etabs(sections)
    assert ret == {0}

# def test_get_section_property_FieldsKeysIncluded():
#     FieldsKeysIncluded = ('Name', 'Material', 'Shape', 'Color', 'Area', 'J', 'I33', 'I22',
#     'I23', 'IMajor', 'IMinor', 'MajorAngle', 'As2', 'As3',
#     'CGOffset3', 'CGOffset2', 'PNAOffset3', 'PNAOffset2',
#     'AMod', 'A2Mod', 'A3Mod', 'JMod', 'I3Mod', 'I2Mod', 'MMod', 'WMod')

#     FieldsKeysIncluded1 = ['Name', 'Material', 'Shape', 'Color', 'Area',
#     'J', 'I33', 'I22', 'I23', 'IMajor', 'IMinor', 'MajorAngle',
#     'As2', 'As3', 'CG Offset 3', 'CG Offset 2', 'PNA Offset 3', 'PNA Offset 2',
#     'Area Modifier', 'As2 Modifier', 'As3 Modifier', 'J Modifier', 'I33 Modifier',
#     'I22 Modifier', 'Mass Modifier', 'Weight Modifier']
#     ret = etabs.get_section_property_FieldsKeysIncluded(FieldsKeysIncluded)
#     assert len(ret) == len(FieldsKeysIncluded1)
#     assert ret == FieldsKeysIncluded1

# @pytest.mark.section
# def test_write_section_names_to_etabs(shayesteh):
#     sections = []
#     for d in (140, 160, 180, 200, 220, 240, 270, 300):
#         sec = Section(d)
#         sections.append(sec)
#     ret = etabs.write_section_names_to_etabs(sections)
#     close_etabs(shayesteh)
#     assert ret == {0}

# # @pytest.mark.section
# def test_apply_sections_to_etabs(shayesteh):
#     sections = [Section(140)]
#     NumFatalErrors, ret = etabs.apply_sections_to_etabs(sections)
#     assert NumFatalErrors == 0
#     assert ret == 0