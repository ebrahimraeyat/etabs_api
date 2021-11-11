__all__ = ['Sections']

class Sections:
    def __init__(
                self,
                SapModel=None,
                etabs=None,
                ):
        if not SapModel:
            self.etabs = etabs
            self.SapModel = etabs.SapModel
        else:
            self.SapModel = SapModel

    def import_sections_to_etabs(self, sections, mat_name='STEEL_CIVILTOOLS'):
        if not sections:
            return
        mat_names = self.SapModel.Propmaterial.GetNameList()[1]
        if not mat_name in mat_names:
            self.SapModel.Propmaterial.SetMaterial(mat_name, 1)
        import tempfile
        default_tmp_dir = tempfile._get_default_tempdir()
        name = 'civiltools.xml'
        from pathlib import Path
        filename = Path(default_tmp_dir) /  name
        section = sections[0]
        section.exportXml(filename, sections)
        ret = set()
        for section in sections:
            name = section.name
            r = self.SapModel.PropFrame.ImportProp(name, mat_name, str(filename), name)
            ret.add(r)
        return ret
            
    # def apply_section_props_to_tabledata(self, TableData, FieldsKeysIncluded, sections):
    #     data = self.etabs.database.reshape_data(FieldsKeysIncluded, TableData)
    #     i_shape = FieldsKeysIncluded.index('Shape')
    #     i_name = FieldsKeysIncluded.index('Name')
    #     for prop in data:
    #         if prop[i_shape] == 'Steel I/Wide Flange':
    #             name = prop[i_name]
    #             for section in sections:
    #                 if section.name == name:
    #                     prop[FieldsKeysIncluded.index('Area')] = str(section.area)
    #                     prop[FieldsKeysIncluded.index('J')] = str(section.J)
    #                     prop[FieldsKeysIncluded.index('I33')] = str(section.Ix)
    #                     prop[FieldsKeysIncluded.index('I22')] = str(section.Iy)
    #                     prop[FieldsKeysIncluded.index('As2')] = str(section.ASy)
    #                     prop[FieldsKeysIncluded.index('As3')] = str(section.ASx)
    #                     prop[FieldsKeysIncluded.index('S33Pos')] = str(section.Sx)
    #                     prop[FieldsKeysIncluded.index('S33Neg')] = str(section.Sx)
    #                     prop[FieldsKeysIncluded.index('S22Pos')] = str(section.Sy)
    #                     prop[FieldsKeysIncluded.index('S22Neg')] = str(section.Sy)
    #                     prop[FieldsKeysIncluded.index('Z33')] = str(section.Zx)
    #                     prop[FieldsKeysIncluded.index('Z22')] = str(section.Zy)
    #                     prop[FieldsKeysIncluded.index('R33')] = str(section.Rx)
    #                     prop[FieldsKeysIncluded.index('R22')] = str(section.Ry)
    #                     prop[FieldsKeysIncluded.index('Cw')] = str(section.cw)
    #                     break
    #     table_data = self.etabs.database.unique_data(data)
    #     return table_data

    # def write_section_names_to_etabs(self, sections, mat_name='STEEL_CIVILTOOLS'):
    #     mat_names = self.SapModel.Propmaterial.GetNameList()[1]
    #     if not mat_name in mat_names:
    #         self.SapModel.Propmaterial.SetMaterial(mat_name, 1)
    #     ret = set()
    #     for section in sections:
    #         d = section.d_equivalentI
    #         bf = section.bf_equivalentI
    #         tw = section.tw_equivalentI
    #         tf = section.tf_equivalentI
    #         name = section.name
    #         r = self.SapModel.PropFrame.SetISection(name, mat_name, d, bf, tf, tw, bf, tf, -1, "", "")
    #         ret.add(r)
    #     return ret 

    # @staticmethod
    # def get_section_property_FieldsKeysIncluded(in_fields):
    #     convert_keys = {
    #         'FilletRad' : 'Fillet Radius',
    #         'CGOffset3' : 'CG Offset 3', 
    #         'CGOffset2' : 'CG Offset 2',
    #         'PNAOffset3': 'PNA Offset 3',
    #         'PNAOffset2': 'PNA Offset 2',
    #         'SCOffset3' : 'SC Offset 3',
    #         'SCOffset2' : 'SC Offset 2',
    #         'AMod' : 'Area Modifier',
    #         'A2Mod' : 'As2 Modifier',
    #         'A3Mod' : 'As3 Modifier',
    #         'JMod' : 'J Modifier',
    #         'I3Mod' : 'I33 Modifier',
    #         'I2Mod' :  'I22 Modifier',
    #         'MMod' : 'Mass Modifier',
    #         'WMod' : 'Weight Modifier',
    #     }

    #     out_fields = []
    #     for f in in_fields:
    #         out_f = convert_keys.get(f, f)
    #         out_fields.append(out_f)
    #     return out_fields

    # def write_section_props_to_etabs(self, sections):
    #     TableKey = 'Frame Section Property Definitions - Summary'
    #     [_, TableVersion, FieldsKeysIncluded, NumberRecords, TableData, _] = self.etabs.database.read_table(TableKey, self.SapModel)
    #     TableData = self.apply_section_props_to_tabledata(TableData, FieldsKeysIncluded, sections)
    #     FieldsKeysIncluded1 = self.get_section_property_FieldsKeysIncluded(FieldsKeysIncluded)
    #     self.SapModel.DatabaseTables.SetTableForEditingArray(TableKey, TableVersion, FieldsKeysIncluded1, NumberRecords, TableData)
    #     NumFatalErrors, ret = self.etabs.database.apply_table()
    #     print(f"NumFatalErrors, ret = {NumFatalErrors}, {ret}")
    #     return NumFatalErrors, ret

    # def apply_sections_to_etabs(self, sections, mat_name='STEEL_CIVILTOOLS'):
    #     self.write_section_names_to_etabs(sections, mat_name)
    #     print('writed sections name to etabs')
    #     self.SapModel.File.Save()
    #     NumFatalErrors, ret =self.write_section_props_to_etabs(sections)
    #     print('writed sections properties to etabs')
    #     return NumFatalErrors, ret
