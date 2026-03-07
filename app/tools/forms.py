from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, SelectField, FieldList, FormField
from wtforms.validators import DataRequired, ValidationError, Length, NumberRange
import enum

class ValidationType(enum.Enum):
    text    = "Text"
    number = "Number"
    lov     = "LOV"

class YesNo(enum.Enum):
    false    = "No"
    true     = "Yes"

class AttributeType(enum.Enum):
    Normal     = "Specification"
    Property   = "Description"


class AttributeForm(FlaskForm):
    class Meta:
        csrf = False

    a_id            = StringField("Attribute ID",       validators=[DataRequired(), Length(max=40)])
    a_name          = StringField("Attribute Name",     validators=[DataRequired(), Length(max=40)])
    ag_id           = StringField("Attribute Group ID", validators=[DataRequired(), Length(max=40)])
    
    a_type          = SelectField("Type",           choices=[(option.name, option.value) for option in AttributeType], validators=[DataRequired()])
    a_multivalued   = SelectField("Multivalued",           choices=[(option.name, option.value) for option in YesNo], validators=[DataRequired()])
    a_external      = SelectField("Externally Maintained", choices=[(option.name, option.value) for option in YesNo], validators=[DataRequired()])
    
    a_purpose       = StringField("Purpose/HelpText",       validators=[Length(max=500)])
    a_valid_on      = StringField("Validity on (Object ID)",    validators=[Length(max=40)])

    a_validation    = SelectField("Validation Base Type",  choices=[(option.name, option.value) for option in ValidationType], validators=[DataRequired()])
    a_lov_id        = StringField("LOV ID",        validators=[Length(max=40)])
    a_min_value     = StringField("Min Value")
    a_max_value     = StringField("Max Value")
    a_max_length    = StringField("Max length")


    def validate_a_lov_id(self, field):
        if self.a_validation.data == "lov" and not field.data:
            raise ValidationError("LOV ID is Mandatory")
        
        
    def validate_a_min_value(self, field):
        if self.a_validation.data == "number" and not field.data:
            raise ValidationError("Mininum is Mandatory")
        elif self.a_validation.data == "number" and not field.data.isdigit():
            raise ValidationError("Mininum should be a number")
        
    def validate_a_max_value(self, field):
        if self.a_validation.data == "number" and not field.data:
            raise ValidationError("Maximum is Mandatory")
        elif self.a_validation.data == "number" and not field.data.isdigit():
            raise ValidationError("Maximum should be a number")
        
    def validate_a_max_length(self, field):
        if self.a_validation.data == "text" and not field.data:
            raise ValidationError("Max Length is Mandatory")
        elif self.a_validation.data == "text" and not field.data.isdigit():
            raise ValidationError("Max Length should be a number")
        
class MyForm(FlaskForm):
    attributes  = FieldList(FormField(AttributeForm), min_entries=1)
    submit      = SubmitField("Generate stepxml")