#!/usr/bin/env python
"""HTML Classes
Based off Seng 265 assignment template and inclass examples
Date: 2024-Apr-5
@Author: lexph
"""

# Python 3.7 and above. Allows forward referencing and stores 
# type hints as string literals instead of expressions.
from __future__ import annotations   

import random as rd
from collections import namedtuple
from enum import Enum
from typing import IO, List, NamedTuple, Dict, Any



class HtmlComponent:
    """HtmlComponent class 
    A base class for all HTML components. It provides a structure for storing 
    the HTML tag, its attributes, and any nested content. It also provides methods for adding nested content 
    and rendering the component as an HTML string.

    Attributes:
        tag (str): The HTML tag for this component.
        tag_attributes (str): Any attributes for the HTML tag.
        content (List[HtmlComponent]): A list of nested HtmlComponent objects.
        level (int): The nesting level of this component.
    """

    def __init__(self, tag: str, content: List[HtmlComponent] = None, level: int = 0, tag_attributes: str = "") -> None:
        """
        Initializes an HtmlComponent.

        Args:
            tag (str): The HTML tag for this component.
            content (List[HtmlComponent], optional): A list of nested HtmlComponent objects. Defaults to None.
            level (int, optional): The nesting level of this component. Defaults to 0.
            tag_attributes (str, optional): Any attributes for the HTML tag. Defaults to "".
        """
        self.tag = tag
        self.tag_attributes = " " + tag_attributes if tag_attributes else ""
        self.content = content if content is not None else []
        self.level = level

    def add(self, component: HtmlComponent) -> None:
        """
        Adds a nested HtmlComponent to this component's content list.
        Updates all nested HtmlComponents indentation level based on parents level.

        Args:
            component (HtmlComponent): The HtmlComponent to add.
        """
        component.level = self.level + 1
        if isinstance (component, HtmlComponent):
            for object in component.content:
                self._update_subclass_level(object, component.level + 1)
        self.content.append(component)   

    def _update_subclass_level(self, component: HtmlComponent, level: int):
        """
        Helper method for recursive updating of subclasses level attribute.

        Args:
            component (HtmlComponent): The HtmlComponent to update.
            level (int): The new level for the component.
        """
        component.level = level
        for object in component.content:
            self._update_subclass_level(object, level + 1)

    def render(self):
        """
        Returns a string representation of this component and all its subcomponents
        as HTML. 

        Returns:
            str: The HTML string.
        """
        indent = '    ' * self.level
        html = ''.join([component.render() for component in self.content])
        return (f'{indent}<{self.tag}{self.tag_attributes}>\n'
                f'{html}'
                f'{indent}</{self.tag}>\n')



class HtmlHead(HtmlComponent):
    """HtmlHead class"""
    def __init__(self, title: str) -> None:
        self.title: str = title
        super().__init__(tag='head')
        self.add(HtmlText(f'<title>{self.title}</title>'))


class HtmlMeta(HtmlComponent):
    """HtmlMeta
    Contains meta data for head"""
    pass


class HtmlBody(HtmlComponent):
    """HtmlBody class"""
    def __init__(self) -> None:
        super().__init__(tag='body')


class HtmlParagraph(HtmlComponent):
    """HtmlParagraph class"""
    def __init__(self, paragraph: str, max_line_len: str = 79) -> None:
        super().__init__(tag='p')
        # Create text objects from inputted paragraph
        for i in range(0, len(paragraph), max_line_len):
            self.add(HtmlText(paragraph[i:i+max_line_len]))


class HtmlDivision(HtmlComponent):
    """HtmlDivision class"""
    def __init__(self, tag_attributes: str = ""):
        super().__init__(tag='div', tag_attributes=tag_attributes)
        

class HtmlText(HtmlComponent):
    """ HtmlText class
        Creates a text object that other classes can use or if svg flag is set to true,
        it creates an svg text object.
    """
    def __init__(self, text: str, as_svg: bool = False, tag_attributes: str = ''):
        self.text = text
        super().__init__(tag='')
        self.svg_open_tag = f'<text {tag_attributes}>' if as_svg else '' 
        self.svg_close_tag = f'</text>' if as_svg else ''

    def render(self) -> str:
        """render() method"""
        indent = '    ' * self.level
        return f'{indent}{self.svg_open_tag}{self.text}{self.svg_close_tag}\n'
    
class HtmlComment(HtmlComponent):
    """HtmlComment class"""
    def __init__(self, text: str):
        self.text = text
        super().__init__(tag='')
    
    def render(self) -> str:
        """render() method"""
        indent = '    ' * self.level
        return f'{indent}<!--{self.text}-->\n'
    
        
class SvgCanvas(HtmlComponent):
    """SvgCanvas class"""
    def __init__(self, width, height, level: int = 1):
        tag_attributes = f'width="{width}" height="{height}"'
        super().__init__(tag='svg', level=level, tag_attributes=tag_attributes)


class ShapeKinds(str, Enum):
    """ShapeKinds class"""
    CIRCLE = 0
    RECTANGLE = 1
    ELLIPSE = 2
    
    def __str__(self) -> str:
        return f'{self.value}'


class Color(NamedTuple):
    """Color class"""
    red: Irange
    green: Irange
    blue: Irange
    opacity: Frange

    def within(self, other: Color) -> bool:
        """within() method"""
        return (self.red.within(other.red) and
                self.green.within(other.green) and
                self.blue.within(other.blue) and
                self.opacity.within(other.opacity)) 
    
    def __str__(self) -> str:
        """__str__() method"""
        return f'{self.red},{self.green},' \
               f'{self.blue},{self.opacity}'


class Irange(NamedTuple):
    """Irange class"""
    imin: int
    imax: int

    def within(self, other: Irange) -> bool:
        """within() method"""
        return (self.imin >= other.imin and
                self.imax <= other.imax)

    def __str__(self) -> str:
        """__str__() method"""
        return f'{self.imin},{self.imax}'


class Frange(NamedTuple):
    """Frange class"""
    fmin: float
    fmax: float

    def within(self, other: Frange) -> bool:
        """within() method"""
        return (self.fmin >= other.fmin and
                self.fmax <= other.fmax)
    
    def __str__(self) -> str:
        """__str__() method"""
        return f'{self.fmin},{self.fmax}'
    

class Extent(NamedTuple):
    """Extent class"""
    x: Irange
    y: Irange

    def within(self, other: Extent) -> bool:
        """within() method"""
        return (self.x.within(other.x) and
                self.y.within(other.y))
    
    def __str__(self) -> str:
        """__str__() method"""
        return f'{self.x},{self.y}'
    
    
def gen_int(r: Irange) -> int:
    """gen_int() function"""
    return rd.randint(r.imin, r.imax)

def gen_float(r: Frange) -> float:
    """gen_float() function"""
    return rd.uniform(r.fmin, r.fmax)


class PyArtConfig:
    """PyArtConfig class
    Creates art configuration objects which set boundaries for generating shapes.
    Class Attributes:
        DEFAULT_COLOR_RANGE (Color): The default color range for the PyArt object.
        DEFAULT_RAD_RANGE (Irange): The default radius range for the PyArt object.
        DEFAULT_ELLIPSE_RAD_RANGE (Extent): The default ellipse radius range for the PyArt object.
        DEFAULT_RWH_RANGE (Extent): The default rectangle width and height range for the PyArt object.
        DEFAULT_POS_RANGE (Extent): The default position range for the PyArt object.
    """
    DEFAULT_COLOR_RANGE = Color(Irange(0, 255), Irange(0, 255), Irange(0, 255), Frange(0, 1.0))
    DEFAULT_RAD_RANGE = Irange(0, 100)
    DEFAULT_ELLIPSE_RAD_RANGE = Extent(Irange(10, 30), Irange(10, 30))
    DEFAULT_RWH_RANGE = Extent(Irange(10, 100), Irange(10, 100))
    DEFAULT_POS_RANGE = Extent(Irange(0, 1000), Irange(0, 2000))
    
    def __init__(self, position: Extent = DEFAULT_POS_RANGE, 
                 shapes: List[ShapeKinds] = [],
                 circle_rad: Irange = DEFAULT_RAD_RANGE,
                 ellipse_rad: Extent = DEFAULT_ELLIPSE_RAD_RANGE,
                 rectangle_wh: Extent = DEFAULT_RWH_RANGE,
                 color: Color = DEFAULT_COLOR_RANGE
                ) -> None: 
        self.shapes: List[ShapeKinds] = shapes
        self.position: Extent = position
        self.rad: Irange = self._verify_range(circle_rad, PyArtConfig.DEFAULT_RAD_RANGE)
        self.radii: Extent = self._verify_range(ellipse_rad, PyArtConfig.DEFAULT_ELLIPSE_RAD_RANGE)
        self.rwh: Extent = self._verify_range(rectangle_wh, PyArtConfig.DEFAULT_RWH_RANGE)
        self.color: Color = self._verify_range(color, PyArtConfig.DEFAULT_COLOR_RANGE)
        
    def _verify_range(self, range1, range2):
        """_verify_range() method
        Validates that the user-defined ranges are within default range values, raises ValueError
        otherwise
        Validates range type as well, raises TypeError if mismatched."""
        if isinstance(range1, type(range2)):
            if(range1.within(range2)):
                return range1
            else:
                raise ValueError(f"Provided range '{range1}' is not within default range '{range2}'")
        else:
            raise TypeError(f"Provided range type '{type(range1)}' does not match default range type '{type(range2)}'")

    def __str__(self) -> str:
        """__str__() method"""
        return f'User-defined art configuration:\n' \
               f'Shapes = [{", ".join(self.shapes)}]\n' \
               f'Position(CXMIN,CXMAX,CYMIN,CYMAX) = ({self.position})\n' \
               f'Radius(RADMIN,RADMAX) = ({self.rad})\n' \
               f'Radii(RADXMIN,RADXMAX,RADYMIN,RADYMAX) = ({self.radii})\n' \
               f'RWH(WMIN,WMAX,HMIN,HMAX) = ({self.rwh})\n' \
               f'Color(REDMIN,REDMAX,GREMIN,GREMAX,BLUMIN,BLUMAX) ' \
               f'= ({self.color.red},{self.color.green},{self.color.blue})\n' \
               f'Opacity(OPMIN,OPMAX) = ({self.color.opacity.fmin:.1f},{self.color.opacity.fmax:.1f})'
               

class Shape(HtmlComponent):
    """Shape class
    Shape base class that contains common attributes and methods shared
    between specific shapes.
    Class Variables:
        Count (int): Total shape count."""
    count: int = 0
    def __init__(self, tag, attributes):
        super().__init__(tag=tag)
        self.attributes = attributes
        self.tag_attributes = self._generate_attributes_str(attributes)
        Shape.count += 1

    def _generate_attributes_str(self, attributes: Dict[str, Any]) -> str:
        """_generate_attributes_str
        Returns a formatted string of of all attributes in the tag"""
        return (' '.join(f'{key}="rgb{str(value)}"' if key == 'fill' 
            else f'{key}="{str(value)}"' for key, value in attributes.items()))

    def render(self):
        """render() method"""
        indent = '    ' * self.level
        return (f'{indent}<{self.tag} {self.tag_attributes}></{self.tag}>\n')


class CircleShape(Shape):
    """CircleShape class"""
    count: int = 0 
    def __init__(self, attributes: Dict[str, Any]) -> None:
        super().__init__(tag='circle', attributes=attributes)
        CircleShape.count += 1

class RectangleShape(Shape):
    """RectangleShape class"""
    count: int = 0          
    def __init__(self, attributes: Dict[str, Any]) -> None:
        super().__init__(tag='rect', attributes=attributes)
        RectangleShape.count += 1
    
class EllipseShape(Shape):
    """EllipseShape class"""
    count: int = 0
    def __init__(self, attributes: Dict[str, Any]) -> None:
        super().__init__(tag="ellipse", attributes=attributes)
        EllipseShape.count += 1


class RandomShape:
    """RandomShape class
    Generates a random shape based on a PyArtConfig object."""
    def __init__(self, art_config: PyArtConfig): 
        self.__shape_kind = rd.choice(art_config.shapes)
        self.attributes = self._gen_random(art_config)
        self.shape = self._gen_shape()

    def _gen_random(self, art_config: PyArtConfig) -> NamedTuple:
        """_gen_random() method"""
        Attributes = namedtuple("Attributes", ["shape_kind", "x", "y", "rad", "rx", "ry", 
                                               "width", "height", "red", "green", "blue", "opacity"])
        return Attributes(shape_kind=self.__shape_kind,
                          x=gen_int(art_config.position.x),
                          y=gen_int(art_config.position.y),
                          rad=gen_int(art_config.rad),
                          rx=gen_int(art_config.radii.x),
                          ry=gen_int(art_config.radii.y),
                          width=gen_int(art_config.rwh.x),
                          height=gen_int(art_config.rwh.y),
                          red=gen_int(art_config.color.red),
                          green=gen_int(art_config.color.green),
                          blue=gen_int(art_config.color.blue),
                          opacity=gen_float(art_config.color.opacity))
        
    def _gen_shape(self) -> Shape:
        """_gen_shape() method
        Creates shape instance based in randomly generated __shape_kind.
        Creates attribute dictionary that gets passed to shape constructor.
        Returns shape object that gets assigned to self.shape attribute."""
        if self.__shape_kind == ShapeKinds.CIRCLE:
            circle_attributes: Dict[str, Any] = {
                'cx': self.attributes.x,
                'cy': self.attributes.y,
                'r': self.attributes.rad,
                'fill': (self.attributes.red, 
                         self.attributes.green, 
                         self.attributes.blue),
                'fill-opacity': self.attributes.opacity
            }
            circle_attributes
            return CircleShape(circle_attributes)
            
        elif self.__shape_kind == ShapeKinds.RECTANGLE:
            rectangle_attributes: Dict[str, Any] = {
                'x': self.attributes.x,
                'y': self.attributes.y,
                'width': self.attributes.width,
                'height': self.attributes.height,
                'fill': (self.attributes.red, 
                         self.attributes.green, 
                         self.attributes.blue),
                'fill-opacity': self.attributes.opacity
            }
            return RectangleShape(rectangle_attributes)
        
        elif self.__shape_kind == ShapeKinds.ELLIPSE:
            ellipse_attributes: Dict[str, Any] = {
                'cx': self.attributes.x,
                'cy': self.attributes.y,
                'rx': self.attributes.rx,
                'ry': self.attributes.ry,
                'fill': (self.attributes.red, 
                         self.attributes.green, 
                         self.attributes.blue),
                'fill-opacity': self.attributes.opacity
            }
            return EllipseShape(ellipse_attributes)
        
        else:
            raise ValueError(f"Cannot find '{self.__shape_kind}' in ShapeKinds enumerators.")
    
    def __str__(self) -> str:
        """__str__() method"""
        return f'Count = ({Shape.count})\n' \
               f'Position(x,y) = ({self.attributes.x},{self.attributes.y})\n' \
               f'Radius(rad) = ({self.attributes.rad})\n' \
               f'Radii(rx,ry) = ({self.attributes.rx},{self.attributes.ry})\n' \
               f'Dimensions(width,height) = ({self.attributes.width},{self.attributes.height})\n' \
               f'Color(r,g,b) = ({self.attributes.red},{self.attributes.green},{self.attributes.blue})\n' \
               f'Opacity(op) = ({self.attributes.opacity})\n' 

    def as_Part2_line(self, set_header: bool = True) -> str:
        """as_Part2_line() method
        Outputs table of Random generated numbers for Shape attributes
        Optional set_header flag to output header row with data"""
        header = f'{"CNT":>3} {"SHA":>3} {"X":>3} {"Y":>3} ' \
                 f'{"RAD":>3} {"RX":>3} {"RY":>3} {"W":>3} ' \
                 f'{"H":>3} {"R":>3} {"G":>3} {"B":>3} {"OP":>3}\n' \
                    if Shape.count == 1 and set_header else ''
        formatted_attrs = []
        for attr in self.attributes:
            if isinstance(attr, float):
                formatted_attrs.append(f'{attr:>3.1f}')
            else:
                formatted_attrs.append(f'{attr:>3}')
        return f'{header}{Shape.count:>3} ' + ' '.join(formatted_attrs)
        
    
    def as_svg(self) -> str:
        """as_svg() method
        Calls render method of randomly generated shape"""
        return self.shape.render()


class HtmlDocument():
    """HtmlDocument class
    Contains methods for creating html document structure
    """
    def __init__(self, title: str = "Default Title") -> None:
        self.head = HtmlHead(title)
        self.body = HtmlBody()
    
    def write_to_file(self, file_name: str) -> None:
        """write_to_file() method"""
        file_name += ".html"
        with open(file_name, 'w') as file:
            file.write("<!DOCTYPE html>\n")
            file.write("<html>\n")
            file.write(self.head.render())
            file.write(self.body.render())
            file.write("</html>\n")


def main():
    """main function"""
    # Create html document:
    doc = HtmlDocument("My Art") 

    # Create a canvas with a certain area
    canvas_width = 500
    canvas_height = 300
    canvas = SvgCanvas(canvas_width, canvas_height)

    # Add comment to start of body
    doc.body.add(HtmlComment("Define SVG drawing box"))
    
    # Art Configuration 3: 
    red_range = Irange(0, 60)
    green_range = Irange(190, 255)
    blue_range = Irange(200, 255)
    opacity_range = Frange(0.0, 0.8)
    color = Color(red=red_range, green=green_range, blue=blue_range, opacity=opacity_range)
    types_of_shapes = [ShapeKinds.CIRCLE, ShapeKinds.RECTANGLE, ShapeKinds.ELLIPSE]
    art_style = PyArtConfig(shapes=types_of_shapes, color=color,
                        position= Extent(Irange(0,canvas_width+10), Irange(0,canvas_height+10)), 
                        circle_rad=Irange(20,80),
                        ellipse_rad=Extent(Irange(10, 15), Irange(25,30)),
                        rectangle_wh=Extent(Irange(30,35), Irange(10,60)))
    canvas.add(RectangleShape(attributes={'width':"100%", 'height':"100%", 'fill':"(251, 72, 196)"}))

    # generate a number of random shapes based on art style
    number_of_shapes: int = 250
    for _ in range(number_of_shapes):
        rand = RandomShape(art_style)
        canvas.add(rand.shape)

    canvas.add(HtmlText(text="Hello World!", as_svg=True, 
                    tag_attributes='x="150" y="150" fill="white" stroke="black" '
                    'font-size="55" font-family="Brush Script MT"'))  

    # Add canvas to body
    doc.body.add(canvas)

    # Open file in write mode, render html components and fill file.
    doc.write_to_file("a41") 


if __name__ == "__main__":
    main()