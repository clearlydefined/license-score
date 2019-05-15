# ClearlyLicensed Metrics

This is the design of license clarity metrics of software components in the
context of the ClearlyDefined project.


Metrics Usage
=============

License clarity metrics are useful for several purposes such as:

- Evaluating the state of license clarity of a publicly available software project.

- Evaluating the overall state of license clarity in aggregations such as
  software repositories (e.g. MavenCentral or GitHub) and major software
  platforms (e.g. JBoss or Qt).

- Determining the level of effort required for the initial curation of license
  data for a ClearlyDefined component.

- Evaluating the reliability of the curated and or detected component metadata.

- Determining the level of effort required for curation of a new version of a
  component that has been previously curated.


Metrics Guiding Principles
==========================

Metrics must be closely aligned with what a ClearlyLicensed open source software
component represents and offer a meaningful indication of license clarity,
through a compound score. 

Metrics should also align with the concept of software project Facets, which
determine the relative importance of the various sections of a software project:

-   core - The files that go into making the release of the component (the deployed code).

-   data - The files included in any data distribution of the component.

-   dev - Files primarily used at development time (e.g. tools, build utilities) and not distributed with the component.

-   docs - Documentation files may be distributed with the main component or separately.

-   examples - Example files may be distributed with the main component or separately.

-   tests - Test files (test code, data and other artifacts) may be distributed with the main component or separately.

The focus for now is only on the core facet when facets are available and in
some cases only on source code in the core facet (as opposed to media files,
scripts, etc.) The metrics could be broken down by facets at a later stage if
needed or consider the relative importance of some facets, such as core that is
more important than other facets such as dev, docs, examples, and tests but this
is not the initial focus.


Metrics Construction and Scaling factors
========================================

The score is:

1. composed of multiple scoring elements that are either binary or progressive.
2. constructed using the weight (total score points) of each scoring element.
3. computed automatically from data collected automatically.
4. bounded between 0 and 100.

There are two types of scoring elements:

- binary elements (e.g. we have a top level license or not, and licenses are
  standard) that grant a fixed number of points. A binary score element wins all
  the assigned weight point if present.

- progressive elements computed with a formula that grants a proportion of a
  score element weight.


Scoring elements discussion
===========================

License clarity scoring elements can include some the following items:

- Clear license information available at the top-level of a project.
- Presence or absence of per-file license and copyright notices or tags.
- Consistency of license information between top-level and per file.
- Presence of complete license texts for all referenced licenses (vs. mentions).
- Use of common, standard license and copyright statements.
- Ease of discovery of license and copyright information by compliance tools.


Clear license declaration at the top-level
------------------------------------------

Open source packages often use text files in a codebase to document the
applicable license(s) for a component. Some common names for these key files are
LICENSE, COPYING, NOTICE, etc.  In other cases a project will use a structured
package manifest file(s) that contain coded or conventional licensing
information (such as a Nuget .nuspec URL, a Maven POM license tags, a Python
setup.py license classification, or an npm package.json license tags). Or there
is a README file that provides semi-structured licensing information. These
files are commonly stored in the root or top-level directory of a package
archive or source code repository.

Collectively the files with either common licensing-related names, readme files
and package manifests are referred to as "key files" when stored at the
top-level or root of a package. These key files are easily discoverable and are
typically the first place where one would look for license information.

The presence of license information in these key files in a form that is easy to
detect mechanically and easy to read by humans contributes to a higher metrics
score.  For instance, a software project without a license notice present at the
top level, but rather in a subdirectory (e.g. "docs"), is not as clearly
licensed as one with a prominent notice found in a file with a common name and
located at the top level of the package code tree.


Discovered
--------------------------------

Beyond top-level license documentation in key files, individual files can
contain explicit license and copyright information making their license clear.

Therefore the presence and proportion of files that can contain licensing
and copyright information and reliably carry such information can be another
element of clarity scoring. By reliably we mean in the sense that these are
reliably detectable by tool(s) with a high level of confidence.

Note that earlier versions were focusing only on source code files rather than
any file type.


License consistency
-------------------

License data is most clear when the top-level or structured license information 
is aligned and in agreement with the aggregated per-file license details.
Therefore scoring should be higher for a software package with coherent and
consistent license top-level and per-file license alignment. Scoring could
also consider the relative importance of some facets, such as core code vs. data.


SPDX standard licenses
----------------------

This is to capture the use of common, standard licenses: a license is considered
as standard if it is present in the SPDX license list.  The use of fully
detectable, standard license notices and texts and copyright statements, as well
as the use of SPDX license identifiers and expressions, contribute to a higher
metrics score. The use of non-detectable, non-standard and less common licenses
makes the licensing less clear.

A custom, non-SPDX license might be a well-crafted piece of legal writing, but
it would have to be reviewed by the user (which, in principle, may have already
reviewed and set policy for the more common SPDX Standard Licenses). 
Needing a review means that the legal terms and conditions are not as clear
as these of more common licenses.


Common copyright notices
------------------------

Having standardized copyright statements contribute to clarity as it becomes
easier to collect. A standard copyright statement is one that can be detected
by tools. A typical copyright statement contains the following elements: 
Copyright [(c)] [year or range of years] [name or names]
The "(c)" or © after the word "Copyright" as well year range are optional.
Note: this is not yet used in the scoring.


Presence of License texts
-------------------------

Most open source licenses require to make available their full license text.
Some packages may contain only license names, a license tag, a license
identifier (such as an SPDX license identifier) or a license notice text but
they may not contain the complete corresponding license text. Clarity is
higher for a software package that contains the full license texts because the
absence of such text would require users to fetch these texts separately. Also
there is no license ambiguity if the full text is provided with the code.

Therefore, capturing the presence of full license texts for any referenced
licenses (vs. notice or mere mentions) is an interesting scoring element.

Also this is clearer when the license texts are present either at the top level
or at well-known, conventional locations within the package.


ClearlyLicensed Scoring Elements
================================

Based on the discussion and definitions above, we have defined five scoring
elements:

## Clearly defined top-level, declared license
------------------------------

A project has specific key file(s) at the top level of its code hierarchy such
as LICENSE, NOTICE or similar (and/or a package manifest) containing structured
license information such as an SPDX license expression or SPDX license
identifier, and the file(s) contain "clearly defined" declared license
information (a license declaration such as a license expression and/or a series
of license statements or notices).  This is a binary score element.


## Discovered
------------------------------

This scoring element is computed as a percentage of files in the core facet of
the project that have both:

 - A license statement such as a text, notice or an SPDX-License-Identifier and, 
 - A copyright statement in standard format that can be detected by tools.

This is a progressive element that is computed based on:
  - LICCOP:  the number of files with a license notice and copyright statement
  - TOT: the total number of files


## License Consistency
-------------------

This scoring element is awarded if all the licenses found anywhere in the core
facet are also found in the top-level key files. This is a binary score element.


## SPDX Standard Licenses
----------------------

This scoring element is awarded if all licenses found in the files of the core
facet are all SPDX-listed licenses. This is a binary score element.


## License Texts
-------------

This scoring element is awarded if there is copy of the full license text
available in one of the key files for every referenced license found in the
core facet. This is a binary score element.


ClearlyLicensed Scoring Formula
===============================

This table describes the formula to compute a value for each of the scoring
elements and the weight of each element.

The total score is the sum of the weights contributed to the score by each
awarded scoring element.

 Scoring element                            | Weight   | Formula   
--------------------------------------------|----------|-----------
[Clearly defined top-level, declared license] (#clearly-defined-top-level,-declared-license) | 30       | binary
[Discovered] (#discovered)            | 25       | LICCOP / TOT
[License Consistency] (#license-consistency)                         | 15       | binary
[SPDX Standard Licenses] (#spdx-standard-licenses)                      | 15       | binary
[License Texts] (#license-texts)                               | 15       | binary



Scoring usage in practice
=========================

Tools Score vs. Effective Score
----------------------------

We amy want to track two scores:

1. A tools score that is computed on the available data collected from a package
   as it exists in the "upstream" project.

2. An effective score that is computed with curated data overlaid when available.

A curation can have several impacts on the score:

- In the most typical case, licensing and copyright may have been reviewed
  and this review has been contributed as part of the curation.

- Updated licensing metadata, notices and copyright may have been created for
  upstream contribution as part of the curation.

- Facets may have been contributed and the computed score is now different for
  the core facet.

We will compute a new effective score based on curated data and in particular:

- Take facets in consideration when facets were contributed as part of the curation.

- Treat a contributed curated top-level license as the new "clearly defined top-level, declared license" scoring element.


Additional Background Material
------------------------------

### Older versions

See https://docs.google.com/document/d/1o_VuVnP1PMoYOXZHSm0TyDX4CsqDXM3zqESAE0AoUnQ/edit# for history and comments.


### ClearlyDefined Project Context

From [https://docs.clearlydefined.io/clearly\#licensed](https://www.google.com/url?q=https://docs.clearlydefined.io/clearly%23licensed&sa=D&ust=1538405356513000) here are some elements of what it means to be "ClearlyLicensed"

Being ClearlyLicensed is a main focus of ClearlyDefined. Many projects have a license. Not all are clearly identified or identified uniformly. Often times there are more licenses at play in the code than are stated in the project. Even when the license is known, the information required to comply with the license (e.g., source location and the parties to the attribution requirement) are not always clear.

This ambiguity results in component users who either end up not following the project requirements or who spend enormous effort trying to "get it right". ClearlyDefined addresses both scenarios by clarifying the license information around a component.

License information is broken down by facet (see below). So if you are consuming just the core of a component (the common case), then you need only be concerned with the licensing data in the core facet.

Each facet includes the following licensing-related information:

-   declared - The SPDX license expression that was declared to cover the component in general. For example, the value of the license property in an NPM or the license declared in the LICENSE file of a Git repo.
-   files - Total number of files related to the facet.
-   discovered - License information found in facet files. In particular, the following properties:

-   expressions - The set of unique SPDX license expressions found across all files in the facet.
-   unknown - The number of files in the facet that have no discernable license information.

-   attribution - Information related to how attribution should be done for the files in the facet. Typically this equates to a list of copyright holders, but projects vary as to how they want attribution to be done.

-   parties - The set of unique entities that are to receive attribution (e.g., copyright holders)
-   unknown - The number of files in the facet that have no discernable attribution information.


### Scoring Discussion

Consider two extreme cases:

1.  a component provides no licensing or copyright information. Nothing at all. This would likely be the lowest score

2.  a component provides explicit licensing or copyright information both in a human and machine form, both at the top level and in every file. The licensing and copyright is detected without ambiguities and all top-level and per-file documentation is consistent. This would likely be the highest score of licensing clarity.

Between these two extreme and likely rare cases we have a continuum of increasingly clear licensing information available with some important thresholds where some usable and consistent set of information is provided.

The selection of which documentation elements contribute to this clarity increase is the essence of the score design.

