#What is the state of open source license clarity?

##Summary
[TODO]

-----------------------------------------------------------------------------------------------

##How obvious and clear is it the license of open source projects?

We designed a license clarity metric 
[https://github.com/clearlydefined/license-score/blob/master/ClearlyLicensedMetrics.md] 

as an attempt to measure this and did evaluate license clarity of about 5000 of
the most popular open source packages. Some of the data we collected confirmed
our intuitions about the state of license clarity but we also made some
surprising discoveries along the way. This is the report of our findings.

Licensing is the essence of open source. Clarity matters a lot as without clear
license terms, an open source package may not be reusable. Actually in the
extreme case where an open source package has no license information, this is no
longer an open source package anymore then there is eventually no permission to
do anything with it. So it is important to get accessed to clear and obvious
licensing information. This makes it easier and more efficient to reuse open
source packages.

But what does it mean for a package to have clear licensing and be "Clearly
Licensed" ?  We designed a scoring procedure such that to get a perfect score
for a package: the license is documented in top-level and well-known key
locations using obvious, non-ambiguous conventions all the code files have a
license and copyright notice the top-level declared licensing is consistent and
aligned with these file-level license notices the licensing is using well-known,
common licenses (e.g. listed at SPDX.org ) the full license text of all the
licenses in use in included in a package archive.

To evaluate license clarity at some scale, we selected about 5000 popular
packages from prominent application package managers: Maven, Pypi, Rubygems, npm
and NuGet. Then we computed their license clarity score as designed [ADD LINK TO
design] and collated all the data details in this CSV [ADD LINK TO CSV]

First, the overall license clarity of these 5K packages is rather low: only 154
of our 4949 packages have a license clarity score of at least 80 (out of a 100
points).  This is not a big surprise as we had a hunch that this was the case
and started the ClearlyDefined project to help improve this. Yet, it is good to
get some confirmation of this fact with actual data.

Of course the criteria we defined for clarity are rather strict: four of the
five scoring elements are binary, winner-takes-all elements, therefore a license
clarity score can degrade fairly quickly. Yet we think that these elements
represent fairly well if the licensing documentation is obvious and clear or if
it requires further review to understand and determine what are the license
terms of an open source package. Practically, when a license score is under
80/100 the license documentation likely requires some additional review,
research and head scratching.
 
Note: ClearlyDefined has a notion of facets such that each file in a software
component can be qualified as being used in development, tests, etc. or is
"core" code. We are not using facets for now, and this introduces further bias
in the results, since a package could have many tests files or build scripts
with less clear licensing than its core code and we do not take this into
account for now.

[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]

Figure 1. Number of packages by license score brackets. 
 
There are only a few (19) packages with a perfect score of 100. Interestingly
all are npm packages. This may be explained by the fact that npm is overall
younger than other package types; npm packages are often smaller (contain fewer
and smaller files); or that the npm tool displays a warning when a license tag
is missing; and that there has been a campaign to document which of the most
popular 1000 npm package were missing a license (See http://npm1k.org/ ).  All
all of the above. We like to think that the the explicit actions taken by the
maintainers of the npm tools and the npm community to provide some feedback on
the lack license clarity has contributed to the overall npm good scores.

When we look at the 90 percentile, we have 65 packages, of which 39 are npms, 23
are from Pypi and 3 from Maven. Rubygems and NuGet have generally low scores and
highest scoring Gem has a score of 54 and the highest scoring NuGet has 60.
[TODO: there is likely a bug for these that we are working on ATM]

Now let's now look at each scoring element separately:
- Clearly defined top-level, declared license
- Available file-level license and copyright
- License Consistency between file and top-level
- SPDX Standard Licenses
- Presence of License Texts

and further break things down by package type.

[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]
[---------------------------------------------------------------------------------- ]

Figure 2. Number of packages in each type for each license scoring element.. 

The worst area is the lack of documentation of a license at the file-level.
There are 3782 out of 4848 packages (about 78%) that have less than 15% of their
file that contain a license notice. But when looking at a breakdown by package
type we can see significant differences.  About 92% of Rubygems packages are in
this case. Anecdotally, Ruby programs seem to contain fewer comments than code
other languages and this seems to extend to license notices, that are usually
comments in the code. In contrast ........ [TODO]

Something that we felt positively surprising at first is the number of packages
using more common, standard SPDX-listed licenses: only 551 of 4848 are using
other licenses. This is rather good, yet we are looking at frequently used,
popular packages. This could well degrade a lot when looking at more packages in
the future. Also some common license terms such as simple public domain
dedications are not listed as SPDX-standard licenses. We would need to make
additional and deeper review to understand the licenses used in the se 551
packages. Again, when we look at the breakdown per package type, there is a
different picture that comes up. Rubygems have a solid coverage 916 out of 999
package use only SPDX licenses.  820 for Maven, 893 for npm ....[TODO]

The consistency between declared and file-level license documentation is also
telling. But this is a somehow a derived element that will not kick in if there
is no declared licensed or no file-level license. As a result, there is no
Rubygem package, no NuGet package and only a handful of Maven packages that are
consistent there [TODO this is weird, we need to revisit]. In contrast there are
153 out of 944 npm packages and 383 out of 984 Pypi packages with a consistent
license documentation. These results mean that using this scoring element may
need to be revisited, though intuitively if makes sense to expect that top-level
and file-level should be consistent and that the top-level should be a summary
of the file-level licensing for a package with clear licensing information.

Rubygem fare much better when it comes to provide a full license text. 258 out
of 996 have it and surprisingly 768 Maven source JARs out of 924 contain their
license texts.  npms do as well as Rubygems with 258 out of 944 and NuGet shines
with 943 out 1000 packages covered [TODO: this is weird and needs to be
revisited] . Pypi does well enough too with 424 out of 984 packages with a
license full text.

No Rubygems has a top-level declared license [TODO: this is a bug which is being
fixed] and only a few Maven JARs (16) have it [TODO: this is a bug too which is
being fixed], and 34 Nuget [TODO: could be a bug??]. In contrast 923 npm of 944
have a license declared which is the best score, and can likely be explained by
the community efforts to provide licensing clarity (npm1k project?). And 835
Pypi packages have such a top license declaration out of 984 which is excellent.


##Improving license clarity

Each time you compute a score or ranking, you eventually creative an incentive
for improvement. That's the intention. With our scoring elements weighting, the
easiest way to bump the license clarity of a package is to provide a top level
declared license ... typically in a package manifest or README that are the
conventional places we would be looking for such documentation.

Scoring element                             | Weight   | style   
--------------------------------------------|----------|-----------
Clearly defined top-level, declared license | 30       | binary
File-level license and copyright            | 25       | progressive
License Consistency                         | 15       | binary
SPDX Standard Licenses                      | 15       | binary
License Texts                               | 15       | binary


Beside this, adding file-level license and copyright notices in our your files
is the next best. This also a progressive socing elements meaning that even if
you add this to only a few files, you get some improvement. A great approach to
do this is to follow the https://reuse.software/ guidelines published by the
Free Software Foundation Europe. Or to check the (new) way of the Linux kernel
maintainers https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/t
ree/Documentation/process/license-rules.rst . Both are building on the SPDX
license identifiers that provide a great way to state a license in a brief and
concise manner. Another easy win is to also ensure that the license text is
present in a package: a brief declaration that a package is using a BSD license
is a good start, but rather ambiguous: that are many variations of the BSD
licenses! Including the full license text in a package is always a good idea for
clarity.
    

##Next steps

The score computation is integrated in ClearlyDefined server-side computation
and it would be great to publish a continuing report and statistics over this
population of packages over time. The interesting information is whether
licensing clarity can improve over time. Furthermore, the scoring is going to be
used as ... [TODO]


## Extra notes on software package types

Each has its own issues wrt. license documentation.

###Maven

The JARs uploaded to the Maven Central repository may not contain the package
manifest (the Maven "pom.xml"). This is not required by Maven and even though
there is a convention to include this manifest in the META-INF subdirectory of a
JAR, few packages do it. We counted only 159 packages out of a thousand that
contained their own pom.xml manifest. As a result, there are only a few Maven
packages that contain a structured license declaration making the overall
clarity low in the Maven  world. The pom file may be available separately from
the Maven repository, but it would be missing from a codebase in most cases when
a JARs is effectively used in a built software application or product.

Furthermore, JARs are typically consumed as compiled binaries that contain
mostly .class files and non of the original licensing files that may exist in
the original project source codebase (such as a git repo). Even source code JARS
seldom contain more than the source code used to compile .class files. Also some
JARs include their license text in the META-INF directory but this is rare too.
To alleviate some of these issues, we used only "source" JARs such to have at
least some license information when this is present in the source code files.
Note that the POM of a JAR uploaded and released on Maven Central is now
required to have license information.

###Rubygems

A Rubygems ".gem" archive is guaranteed to contain a YAML-structured metadata
file (derived from the ".gemspec" manifest found in the source code repository).
However, declaring a license tag is not required. Furthermore, this license tag
is not fully specified and this leads to ambiguities: this tag is a list of
licenses strings, but there is no indication in the Rubygems specification that
defines what is the relationship between multiple licenses when there is more
than one: do all licenses apply? or is this a choice? The license scanner
(ScanCode toolkit) assumes by default that all the licenses apply (e.g. this is
a conjunction of multiple licenses). This is unlikely true in all cases, but
short of clarity in the Rubygems specification or other contextual information
available in a given package there is not much more we can do. This does not
have a direct impact on the clarity of the score though it could be something
that could be lower the score of a Rubygems with multiple licenses in the
future.

###Pypi

Python packages come in various forms. The two primary forms are the built
"wheel" archive and the source distribution archive. Because not all packages
are available as wheels, we have used source distributions instead of wheels:
these are tarballs created from the development source code files and should
typically contain a package manifest and other documentation files. The manifest
is typically a "setup.py" Python file that contain some structured license
information. No  license information is required to release publicly a package
on Pypi. Note also that the wheels packaging does not automatically include a
license text that may be present in the source code checkout making it less
clear liecnse-wise.

###npm

An npm JavaScript package archives always contains a "package.json" manifest.
This manifest has a license tag, but that tag is not mandatory when uploading a
package (but at least a warning is reported if a package.json has no license
information).. When present, the license should be an SPDX license expression
(but there are some exceptions to this). As a result, npms more often have well
defined top-level declared licensing than other packages that may not enforce a
standard to document licensing information.

###NuGet

A .Net NuGet package archive always contains a ".nuspec" manifest. This manifest
only support a license URL to document licenses which is rather limited. Nuget
packages contain mostly compiled binaries but can also include additional text
files (such as for license texts).


##Reproducing the score computation results

To reproduce the computations used in this article, use the scripts and
instructions provided in the https://github.com/clearlydefined/license-score/
repository.

Beyond this, the score computation have been integrated in the ClearlyDefined
server code. When browsing a component definition details at
https://clearlydefined.io/definitions there is a Licensed badge that comes with
two scores: the base score as computed on the base package and a "curated" score
that is computed on the updated package if it has been curated and reviewed.


##Selecting popular packages...

The selection of 1000 popular packages for each type is more an art than a
science. In some cases, a public package repository provides some indication of
popularity such as a number of downloads. We used this even though that may be a
weak indicator of the real popularity for a package. In some other cases (such
as Maven central) there is little information available. We tried then to check
if a package manifest contained some other clues (such as a reference to GitHub
repo) and used the stars and fork counts on the corresponding repo as a proxy
for popularity.


##Credits

Many thanks to ....

