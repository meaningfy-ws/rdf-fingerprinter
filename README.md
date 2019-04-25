
**Understand** the structure of your RDF data at a glance using automatically built **application profiles** and spot differences between dataset profiles. 

An [_application profile_](https://en.wikipedia.org/wiki/Application_profile), in this context, is the set of [_data shapes_](https://www.w3.org/2014/data-shapes/wiki/Main_Page) designed for a particular purpose acting as constraints on how the data are instantiated and so can be used to validate the data.

_Fingerprinting_ is the action of generating, or rather, guessing, the application profile applied to a particular dataset. This is an inductive process of reconstructing the data shape for each class instantiated in the dataset. 

# Installation
RDF fingerprinter may be installed with pip as follows. (Because ,this project is still in Alpha stage, the installation is available for the moment from sources only.)
 
```
git clone https://github.com/costezki/RDF-fingerprint-diff.git
cd RDF-fingerprint-diff
pip install . 
```

This project currently supports python 3.6 or later.  

# Getting started

At the moment the fingerprinter is able to deliver the core functionality which is generate the fingerprint of an RDF dataset structured as an application profile. To launch it follow the following steps (In the future this process will be simplified). The detailed documentation is available [here](https://github.com/costezki/RDF-fingerprint-diff/wiki/Application-profile-project)

1. Create a project folder.    
2. Prepare the input data by running [this SPARQL query](https://github.com/costezki/RDF-fingerprint-diff/blob/master/resources/query/fingerprint.rq) on the target dataset(s).    
3. (optional) Tweak the _configuration.json_ file. 
4. Run the fingerprinter in the project folder.

Details on each of the steps are available [here](https://github.com/costezki/RDF-fingerprint-diff/wiki/Application-profile-project).

An example project is available [here](https://github.com/costezki/RDF-fingerprint-diff/tree/master/examples/fingerprinter_jinja/pub_css_ap). It is is based on HTML5/CSS template using [Pub-CSS](https://github.com/thomaspark/pubcss) styling.  Please feel free to copy and modify this project as needed. The document template (in /fragments sub-folder) is built using [Jinja2 templating language](http://jinja.pocoo.org/docs/2.10/).   

# Envisioned development 
* [architectural sketch](https://github.com/costezki/RDF-fingerprint-diff/wiki/Specifications)
* [future features](https://github.com/costezki/RDF-fingerprint-diff/wiki/Future-features)

# Licence 
_RDF Fingerprinter_ is freely distributable under the terms of the [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.en.html)