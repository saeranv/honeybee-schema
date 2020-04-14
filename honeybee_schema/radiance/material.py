# TODO: change to Modifers Schema?
"""Material Schema"""
from pydantic import Field, constr, validator, root_validator
from typing import List, Union

from .._base import IDdBaseModel, BaseModel


class Void(BaseModel):
    """Void modifier"""

    type: constr(regex='^void$') = 'void'


class ModifierBase(IDdBaseModel):
    """Base class for Radiance Modifiers"""

    modifier: Union[
         Void, 'Plastic', 'Glass', 'BSDF', 'Glow', 'Light', 'Trans'
    ] = Field(
        default=Void(),
        description='Material modifier (default: Void).'
        )

    dependencies: List[
        Union[Void, 'Plastic', 'Glass', 'BSDF', 'Glow', 'Light', 'Trans']
    ] = Field(
        default=[],
        description='List of modifiers that this modifier depends on. '
                    'This argument is only useful for defining advanced modifiers '
                    'where the modifier is defined based on other modifiers '
                    '(default: []).'
        )


class Plastic(ModifierBase):
    """Radiance plastic material."""

    type: constr(regex='^plastic$') = 'plastic'

    r_reflectance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the red channel reflectance '
                    '(default: 0).'
    )

    g_reflectance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the green channel reflectance '
                    '(default: 0).'
    )

    b_reflectance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the blue channel reflectance '
                    '(default: 0).'
    )

    specularity: float = Field(
        default=0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the fraction of specularity. '
                    'Specularity fractions greater than 0.1 are not realistic. '
                    '(default: 0).'
    )

    roughness: float = Field(
        default=0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the roughness, specified as the '
                    'rms slope of surface facets. Roughness greater than 0.2 are '
                    'not realistic (default: 0).'
    )


class Trans(Plastic):
    """Radiance Translucent material."""

    type: constr(regex='^trans$') = 'trans'

    transmitted_diff: float = Field(
        default=0,
        ge=0,
        le=1,
        description='The fraction of transmitted light that is transmitted diffusely in '
                    'a scattering fashion (default: 0).'
    )

    transmitted_spec: float = Field(
        default=0,
        ge=0,
        le=1,
        description='The fraction of transmitted light that is not diffusely scattered '
                    '(default: 0).'
    )

    @root_validator
    def check_sum_fractions(cls, values):
        """Ensure sum is less than 1."""
        trans_diff = values.get('transmitted_diff')
        trans_spec = values.get('transmitted_spec')
        r_refl = values.get('r_reflectance')
        g_refl = values.get('g_reflectance')
        b_refl = values.get('b_reflectance')
        identifier = values.get('identifier')
        summed = trans_diff + trans_spec + r_refl + g_refl + b_refl
        assert summed <= 1, 'The sum of the transmitted diffuse and specular light ' \
            'fractions cannot be greater than 1, but is {} for modifier {}.'.format(
                summed, identifier)
        return values


class Glass(ModifierBase):
    """Radiance glass material."""

    type: constr(regex='^glass$') = 'glass'

    r_transmissivity: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the red channel transmissivity '
                    '(default: 0).'
    )

    g_transmissivity: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the green channel transmissivity '
                    '(default: 0).'
    )

    b_transmissivity: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the blue channel transmissivity '
                    '(default: 0).'
    )

    refraction_index: float = Field(
        default=1.52,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the index of refraction '
                    '(default: 1.52).'
    )


class BSDF(ModifierBase):
    """Radiance BSDF (Bidirectional Scattering Distribution Function) material."""

    type: constr(regex='^BSDF$') = 'BSDF'

    up_orientation: List[float] = Field(
        default=(0.01, 0.01, 1.00),
        min_items=3,
        max_items=3,
        description='Vector as sequence that sets the hemisphere that the BSDF material '
                    'faces. (default: (0.01, 0.01, 1.00).'
    )

    thickness: float = Field(
        default=0,
        description='Optional number to set the thickness of the BSDF material '
                    'Sign of thickness indicates whether proxied geometry is '
                    'behind the BSDF surface (when thickness is positive) or in '
                    'front (when thickness is negative)(default: 0).'
    )

    function_file: str = Field(
        default='.',
        min_length=1,
        max_length=100,
        description='Optional input for function file (default: ".").'
    )

    transform: str = Field(
        default=None,
        min_length=1,
        max_length=100,
        description='Optional transform input to scale the thickness and reorient '
                    'the up vector (default: None).'
    )

    bsdf_data: bytes = Field(
        ...,
        description='BSDF xml file data as bytes.'
    )

    front_diffuse_reflectance: List[float] = Field(
        default=None,
        min_items=3,
        max_items=3,
        description='Optional additional front diffuse reflectance as sequence of '
                    'numbers (default: None).'
    )

    back_diffuse_reflectance: List[float] = Field(
        default=None,
        min_items=3,
        max_items=3,
        description='Optional additional back diffuse reflectance as sequence of '
                    'numbers (default: None).'
    )

    diffuse_transmittance: List[float] = Field(
        default=None,
        min_items=3,
        max_items=3,
        description='Optional additional diffuse transmittance as sequence of '
                    'numbers (default: None).'
    )

    @validator('front_diffuse_reflectance')
    def check_front_diff_value(cls, values):
        """Ensure every list value is between 0 and 1."""
        assert all(0 <= v <= 1 for v in values), \
            'Every value in front diffuse reflectance must be between 0 and 1.'
        return values

    @validator('back_diffuse_reflectance')
    def check_back_diff_value(cls, values):
        """Ensure every list value is between 0 and 1."""
        assert all(0 <= v <= 1 for v in values), \
            'Every value in back diffuse reflectance must be between 0 and 1.'
        return values

    @validator('diffuse_transmittance')
    def check_diff_trans_value(cls, values):
        """Ensure every list value is between 0 and 1."""
        assert all(0 <= v <= 1 for v in values), \
            'Every value in diffuse transmittance must be between 0 and 1.'
        return values


class Light(ModifierBase):
    """Radiance Light material."""

    type: constr(regex='^light$') = 'light'

    r_emittance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the red channel of the modifier '
                    '(default: 0).'
    )

    g_emittance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the green channel of the modifier '
                    '(default: 0).'
    )

    b_emittance: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description='A value between 0 and 1 for the blue channel of the modifier '
                    '(default: 0).'
    )


class Glow(Light):
    """Radiance Glow material."""

    type: constr(regex='^glow$') = 'glow'

    max_radius: float = Field(
        default=0,
        description='Maximum radius for shadow testing (default: 0). Surfaces with zero '
                    'will never be tested for zero, although it may participate in '
                    'interreflection calculation. Negative values will never contribute '
                    'to scene illumination.'
    )


# Required for self.referencing model
# see https://pydantic-docs.helpmanual.io/#self-referencing-models
ModifierBase.update_forward_refs()
Plastic.update_forward_refs()
Glass.update_forward_refs()
BSDF.update_forward_refs()
Glow.update_forward_refs()
Light.update_forward_refs()
Trans.update_forward_refs()

