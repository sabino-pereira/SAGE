from flask import Flask, render_template, flash, send_file, request
from forms import MyForm
import io

"""
Variables for various tasks
"""
file_path = "output/attributes.xml"

stepxml_start = """<?xml version="1.0" encoding="UTF-8"?>
<STEP-ProductInformation ContextID="Context1" WorkspaceID="Main" UseContextLocale="false">
  <AttributeList>
"""

stepxml_end = """
  </AttributeList>
</STEP-ProductInformation>
"""


file_data_attribute = """\n
    <Attribute ID="{}" MultiValued="{}" ProductMode="{}" FullTextIndexed="false" ExternallyMaintained="{}" Derived="false" Selected="true" Referenced="true" Mandatory="false">
      <Name>{}</Name>
      <Validation BaseType="number" MinValue="1" MaxValue="100" MaxLength="" InputMask="">
      <AttributeGroupLink AttributeGroupID="{}"/>
      <UserTypeLink UserTypeID="Variant"/>
    </Attribute>
"""








"""
Main Code
"""
flaskApp = Flask(__name__)
flaskApp.secret_key = "lkasjdflk978&^&()oasdfasdf"

# Main Route
@flaskApp.route("/", methods=["GET", "POST"])
def home():
    form = MyForm()
    
    if request.method == "POST":
        if form.validate_on_submit():
            buffer = io.BytesIO()               
                
            # Add top XML
            buffer.write(stepxml_start.encode('utf-8'))

            # Iterate thorugh the user inputs and add what's needed
            for attribute in form.attributes.data:                    
                
                attributeHeaderString  = '\n    <Attribute ID="{}" MultiValued="{}" ProductMode="{}" FullTextIndexed="false" ExternallyMaintained="{}" Derived="false" Selected="true" Referenced="true" Mandatory="false">'.format(attribute["a_id"], attribute["a_multivalued"], attribute["a_type"], attribute["a_external"])
                attributeNameString    = '\n      <Name>{}</Name>\n      '.format(attribute["a_name"])
                
                if attribute["a_validation"] == "text":
                    attributeValidationString = '<Validation BaseType="text" MinValue="" MaxValue="" MaxLength="{}" InputMask=""/>'.format(attribute["a_max_length"])
                elif attribute["a_validation"] == "number":
                    attributeValidationString = '<Validation BaseType="number" MinValue="{}" MaxValue="{}" MaxLength="" InputMask=""/>'.format(attribute["a_min_value"], attribute["a_min_value"])
                elif attribute["a_validation"] == "lov":
                    attributeValidationString = '<ListOfValueLink ListOfValueID="{}"/>'.format(attribute["a_lov_id"])                 
                
                if attribute["a_purpose"]:
                    attributeMetadataString = """
    <MetaData>
      <Value AttributeID="AttributeHelpText">{}</Value>
      <Value AttributeID="Purpose">{}</Value>
    </MetaData>""".format(attribute["a_purpose"], attribute["a_purpose"])
                
                else:
                    attributeMetadataString = ""
                
                
                attributeGroupString   = '\n      <AttributeGroupLink AttributeGroupID="{}"/>'.format(attribute["ag_id"])
                
                if attribute["a_valid_on"]:
                    attrbuteValidityString = '\n      <UserTypeLink UserTypeID="{}"/>'.format(attribute["a_valid_on"])
                else:
                    attrbuteValidityString = ""
                attributeFooterString  = '\n    </Attribute>\n'
                
                
                final_string = attributeHeaderString + attributeNameString + attributeValidationString + attributeMetadataString + attributeGroupString + attrbuteValidityString + attributeFooterString
                buffer.write(final_string.encode('utf-8'))
                   
            # Add Bottom XML
            buffer.write(stepxml_end.encode('utf-8')) 
            
            buffer.seek(0)
            
            return send_file(
                buffer,
                as_attachment=True,
                download_name='attributes-list.xml',
                mimetype='text/plain'
            )
            flash("Generated stepxml and written to file. You can now download it.", "success")
        else:
            flash("Something went check, check the form for indicated errors.", "danger")

    
    
    return render_template("attributes.html", form=form)




# # Download File Route
# @flaskApp.route('/download')
# def download_file():
#     return send_file(file_path, as_attachment=True)
