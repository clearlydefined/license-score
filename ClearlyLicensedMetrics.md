ClearlyLicensed Metrics

This document is the proposal to design license clarity metrics for software
components in the context of the ClearlyDefined project.

Metrics Usage
=============

License clarity metrics are useful for several purposes such as:

-   Evaluating the state of license clarity of a publicly available software project.
-   Evaluating the overall state of license clarity in aggregations such as software repositories (e.g. MavenCentral or GitHub) and major software platforms (e.g. JBoss or Qt).
-   Determining the level of effort required for the initial curation of license data for a ClearlyDefined component.
-   Evaluating the reliability of the curated and or detected component metadata.
-   Determining the level of effort required for curation of a new version of a component that has been previously curated.

Metrics Guiding Principles
==========================

Metrics must be closely aligned with what a ClearlyLicensed open source software component represents and offer a meaningful indication of license clarity, through a compound score. 

Metrics should also align with the concept of software project Facets, which determine the relative importance of the various sections of a software project:

-   core - The files that go into making the release of the component (the deployed code).
-   data - The files included in any data distribution of the component.
-   dev - Files primarily used at development time (e.g. tools, build utilities) and not distributed with the component.
-   docs - Documentation files may be distributed with the main component or separately.
-   examples - Example files may be distributed with the main component or separately.
-   tests - Test files (test code, data and other artifacts) may be distributed with the main component or separately.

The focus for now is only on the core facet when facets are available and in some cases only on source code in the core facet (as opposed to media files, scripts, etc.) The metrics could be broken down by facets at a later stage if needed or consider the relative importance of some facets, such as core that is more important than other facets such as dev, docs, examples, and tests but this is not the initial focus.

Metrics Score and Scaling factors
---------------------------------

The score is:

1.  bounded between 0 and 100.
2.  composed of multiple scoring elements that are either binary or progressive.
3.  constructed using the weight (total score points) of each element.
4.  computed automatically from available data that are either  collected automatically or updated from a curation.

There are two types of scoring elements:

-   binary elements (e.g. we have a top level license or not, and licenses are standard) that grant a fixed number of points. A binary score element wins all the assigned weight point if present.
-   progressive elements computed with a formula that grants a proportion of a score element weight.

Scoring elements discussion
===========================

License clarity scoring elements can include some the following items:

-   Clearly defined top-level, declared license
-   Presence of file-level license and copyright
-   License consistency between top level and file-level licenses
-   Presence and coverage of full license texts for referenced licenses (vs. mentions).
-   Use of standard license and copyright information texts (e.g. use of SPDX license identifiers/expressions, use of detectable and standard license notices and copyright statements, etc.).
-   Ease of discovery of license and copyright information by compliance tools.


Clearly defined top-level, declared license
-------------------------------------------

This is based on the presence and clarity of license information in key, top-level project files.

Open source packages often use text files in a codebase to document the applicable license(s) for a component. Some common names for these key files are LICENSE, COPYING, NOTICE, etc.  In other cases a project will use a structured package manifest file(s) that contain coded or conventional licensing information (such as a Nuget .nuspec URL, a Maven POM license tags, a Python setup.py license classification, or an npm package.json license tags). Or there is a README file that provides semi-structured licensing information. These files are commonly stored in the root or top-level directory of a package archive or source code repository.

Collectively the files with either common licensing-related names, readme files and package manifests are referred to as "key files" when stored at the top-level or root of a package. These key files are easily discoverable and are typically the first place where one would look for license information.

The presence of license information in these key files in a form that is easy to detect mechanically and easy to read by humans contributes to a higher metrics score.  For instance, a software project without a license notice present at the top level, but rather in a subdirectory (e.g. "docs"), is not as clearly licensed as one with a prominent notice found in a file with a common name and located at the top level of the package code tree.

File-level license and copyright
--------------------------------

This is based on the presence, clarity and coverage of per-file license and copyright information to answer this question:

Do files that can contain licensing and copyright information reliably carry such information in the sense that these are reliable detected by tools?

Beyond top-level documentation of licensing in key files, individual files can (and should when this is possible) contain license and copyright information. The presence and proportion of files that have such per-file information is another metrics score element.

Note that earlier versions were focusing only on source code files rather than any file type.

License consistency
-------------------

This is to capture the coherence and alignment of top-level, key file information with file-level licensing information.

License data is most clear when the top-level or structured license information  is aligned and in agreement with the aggregated per-file details. Metrics scoring is higher for a software package with accurate license alignment, and the scoring should consider the relative importance of some facets, such as core code and data.


SPDX standard licenses
----------------------

This is to capture the use of standard licenses: a license is considered as standard if it is present in the SPDX license list.  The use of fully detectable, standard license notices and texts and copyright statements, as well as the use of SPDX license identifiers and expressions, contribute to a higher metrics score. The use of non-detectable, non-standard licenses makes the licensing less clear.

A custom, non-SPDX license might be a well-crafted piece of legal writing, but it would have to be reviewed by the user (which, in principle, has may already has reviewed and set policy for the SPDX Standard Licenses), then it means that the legal terms and conditions are not so clearly defined.

A standard copyright statement is one that can be detected by tools. A typical copyright statement contains the following elements: Copyright [(c)] [year or range of years] [name or names]. The "(c)" or © after the word "Copyright" are optional. The year range is optional. This is not yet used in the scoring.


License texts
-------------

This is to capture the presence of full license texts for any referenced licenses (vs. notice or mere mentions) found in a  package.

Most open source licenses require to make available their full license text. Some packages may contain only license names, a license tag, a license identifier (such as an SPDX license identifier) or a license notice text but they may not contain the complete corresponding license text. Metrics scoring is higher for a software package that contains the full license texts because the absence of such text would require users to fetch these texts separately. Also there could be some ambiguity if the full text is not provided.


ClearlyLicensed Scoring Formula
===============================

We have defined five scoring elements based on the above:

###### Clearly defined top-level, declared license: 
 
A project has specific key file(s) at the top level of its code hierarchy such as LICENSE, NOTICE or similar (and/or a package manifest) containing structured license information such as an SPDX license expression or SPDX license identifier, and the file(s) contain "clearly defined" declared license information 
(a license declaration such as a license expression and/or a series of license statements or notices). This is a binary score element.


# File-level license and copyright: 

Do files that can contain licensing and copyright information reliably carry such information? 

This is based on a percentage of files in the core facet of the project that have both:
   - A license statement such as a text, notice or an SPDX-License-Identifier and, 
   - A copyright statement in standard format  that can be detected by tools.

Here "reliably" means that these are reliably detected by tool(s) with a high level of confidence.
This is a progressive element that is computed based on:
  - LICCOP:  the number of files with a license notice and copyright statement
  - TOT: the total number of files


# License Consistency:

Are all file-level licenses consistent and documented in top-level key files?
This is based on files in the core facet. This is a binary score element awarded if all the licenses found anywhere in the core facet are also found in the top-level key files.


# SPDX Standard Licenses:


Are all the licenses standard SPDX-listed licenses? 
This is based on files in the core facet. This is a binary score element awarded if all the licenses found anywhere in the core facet use an SPDX-listed license, identified by a standard license notice or the SPDX identifier.


# License Texts:

Is a copy of the complete license text available in the project for every referenced license?

This is based on files in the core facet. This is a binary score element awarded if the package contains the full license text  for all the licenses found anywhere in the core facet.


And this table describes the formula to compute a value for each of the scoring
elements and the weight of each element.

The total score is the sum of the weight contributed to the score by each element.

 Scoring element                            | Weight   | Formula   
--------------------------------------------|----------|-----------
Clearly defined top-level, declared license | 30       | binary
File-level license and copyright            | 25       | LICCOP / TOT
License Consistency                         | 15       | binary
SPDX Standard Licenses                      | 15       | binary
License Texts                               | 15       | binary



Base Score vs. Curated Score
----------------------------

1.  Base score is computed on the available data collected from a package as it exists "upstream", as redistributed by the project.
2.  Curated score is computed from the combination of the initial base score and the curated data overlaid.

A curation can have several impacts on the score:

-   In the most typical case, licensing and copyright may have been reviewed and this review has been contributed as part of the curation.
-   Updated licensing metadata, notices and copyright may have been created for upstream contribution as part of the curation.
-   Facets may have been contributed and the computed score is now different for the core facet.

We will compute a new Curated score based on curated data and in particular:

-   Take facets in consideration when facets were contributed as part of the curation.
-   Treat a contributed curated top-level license as the new "clearly defined top-level, declared license" scoring element.


Additional Background Material
------------------------------

### Older versions

See https://docs.google.com/document/d/1o_VuVnP1PMoYOXZHSm0TyDX4CsqDXM3zqESAE0AoUnQ/edit# for history and comemnts.


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

