# Preview: assertions for `inbox_820f624e0b0884af` before commit

1 deterministic assertion(s) in this run's slice. Each row is one event; the grounding span column is filled by an extraction stage and is empty for deterministic assertions.

| kind | class | key | properties | method | grounding span |
|---|---|---|---|---|---|
| node | Document | `inbox_820f624e0b0884af` | doc_id=inbox_820f624e0b0884af, title=Web Linking (RFC 8288), local_path=intake/inbox/rfc8288.txt, sha256=820f624e0b0884af5c732e8087a65182452e49f2, disposition=reference, doc_type=standard | manifest |  |

## Proposed by extraction

232 segment(s) extracted: 164 grounded, 65 kept_out, 3 ungrounded. Located spans are cut from the parsed text by the harness; the model supplied a locator. **will be committed: 164** (status `proposed`, stage 11a); everything else is recorded in the evidence file and never enters the ledger.

| kind | class | segment | claim kind | located text | extractor | grounding span |
|---|---|---|---|---|---|---|
| proposed | Claim | None None | Standard | Internet Engineering Task Force (IETF)                     M. Nottingham Request for Comments: 8288                                  October 2017 Obsoletes: 5988 Category: Standards Track |  | [6:193] sha256 a9f8b5b7e921 |
| proposed | Claim | None None | Concept | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [268:430] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [268:430] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | It also defines the serialisation of such links in HTTP headers with    the Link header field. |  | [435:529] sha256 5bf6748bcc34 |
| proposed | Claim | None None | Concept | It also defines the serialisation of such links in HTTP headers with    the Link header field. |  | [435:529] sha256 5bf6748bcc34 |
| proposed | Claim | None None | Concept | This document is a product of the Internet Engineering Task Force    (IETF). |  | [605:681] sha256 10e473f3ef71 |
| proposed | Claim | None None | Definition | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [268:430] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [5629:5791] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [5629:5791] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | Furthermore, Section 3 defines an HTTP header field for conveying    such links. |  | [6018:6098] sha256 41fc05f8b1b0 |
| proposed | Claim | None None | Definition | This specification defines a model for the relationships between    resources on the Web ("links") and the type of those relationships    ("link relation types"). |  | [5629:5791] sha256 7fd7059b6fde |
| proposed | Claim | None None | Concept | The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",    "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and    "OPTIONAL" in this document are to be interpreted as described in BCP |  | [6133:6345] sha256 bfd9123084bc |
| proposed | Claim | None None | Concept | This document uses the Augmented Backus-Naur Form (ABNF) [RFC5234]    notation of [RFC7230], including the #rule, and explicitly includes    the following rules from it: quoted-string, token, SP (space), BWS    (bad whitespace), OWS (optional whitespace), RWS (required    whitespace), LOALPHA, DIGIT. |  | [6444:6745] sha256 94cc37ca5727 |
| proposed | Claim | None None | Definition | The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT",    "SHOULD", "SHOULD NOT", "RECOMMENDED", "NOT RECOMMENDED", "MAY", and    "OPTIONAL" in this document are to be interpreted as described in BCP |  | [6133:6345] sha256 bfd9123084bc |
| proposed | Claim | None None | Standard | The requirements regarding conformance and error handling highlighted    in [RFC7230], Section 2.5 apply to this document. |  | [7039:7161] sha256 7a7b06cc4738 |
| proposed | Claim | None None | Concept | In this specification, a link is a typed connection between two    resources and is comprised of: |  | [7338:7435] sha256 dd7113e16eaa |
| proposed | Claim | None None | Concept | o  a link context,    o  a link relation type (Section 2.1),    o  a link target, and    o  optionally, target attributes (Section 2.2). |  | [7440:7576] sha256 e2224fb1faa2 |
| proposed | Claim | None None | Concept | o  a link context,    o  a link relation type (Section 2.1),    o  a link target, and    o  optionally, target attributes (Section 2.2). |  | [7440:7576] sha256 e2224fb1faa2 |
| proposed | Claim | None None | Concept | o  a link context,    o  a link relation type (Section 2.1),    o  a link target, and    o  optionally, target attributes (Section 2.2). |  | [7440:7576] sha256 e2224fb1faa2 |
| proposed | Claim | None None | Concept | o  a link context,    o  a link relation type (Section 2.1),    o  a link target, and    o  optionally, target attributes (Section 2.2). |  | [7440:7576] sha256 e2224fb1faa2 |
| proposed | Claim | None None | Concept | Links are conveyed in link serialisations; they are the "bytes on the    wire", and can occur in various forms. |  | [8849:8960] sha256 49d7e8539896 |
| proposed | Claim | None None | Concept | Finally, links are used by link applications. |  | [9411:9456] sha256 3c984902daeb |
| proposed | Claim | None None | Concept | Registered relation type names MUST conform to the reg-rel-type rule    (see Section 3.3) and MUST be compared character by character in a    case-insensitive fashion. |  | [11467:11634] sha256 c7db63b4fd63 |
| proposed | Claim | None None | Concept | The "Link Relations" registry is located at    <https://www.iana.org/assignments/link-relations/>. |  | [12922:13020] sha256 1f2c2a8ff23d |
| proposed | Claim | None None | Concept | application "Web browsing" looks for the "stylesheet" link relation    type in the HTML link serialisation (and optionally in the Link    header field), whereas the application "AtomPub" uses the "edit" and    "edit-media" link relations in the Atom serialisation. |  | [9773:10037] sha256 a0d05cd87c3d |
| proposed | Claim | None None | Definition | In this specification, a link is a typed connection between two    resources and is comprised of: |  | [7338:7435] sha256 dd7113e16eaa |
| proposed | Claim | None None | Definition | In the simplest case, a link relation type identifies the semantics    of a link. |  | [10069:10150] sha256 d871bc2fa151 |
| proposed | Claim | None None | Claim | This specification does not place restrictions on the cardinality of    links; there can be multiple links to and from a particular target    and multiple links of the same or different types between a given    context and target. |  | [8327:8557] sha256 587263dba661 |
| proposed | Claim | None None | Claim | Registered relation type names MUST conform to the reg-rel-type rule    (see Section 3.3) and MUST be compared character by character in a    case-insensitive fashion. |  | [11467:11634] sha256 c7db63b4fd63 |
| proposed | Claim | None None | Claim | Registrations MUST reference a freely available, stable    specification. |  | [13926:13999] sha256 6be8b2fb796c |
| proposed | Claim | None None | Claim | Relation types SHOULD NOT infer any additional semantics based upon    the presence or absence of another link relation type, or its own    cardinality of occurrence. |  | [10855:11021] sha256 e80263685406 |
| proposed | Claim | None None | Claim | Relation types are not to be confused with media types [RFC2046];    they do not identify the format of the representation that results    when the link is dereferenced. |  | [10594:10763] sha256 d8cc7c0d1155 |
| proposed | Claim | None None | Concept | Note that relation types can be registered by third parties    (including the expert(s)), if the expert(s) determines that an    unregistered relation type is widely deployed and not likely to be    registered in a timely manner otherwise. |  | [14004:14243] sha256 1650cc6c1eab |
| proposed | Claim | None None | Concept | Applications that don't wish to register a relation type can use an    extension relation type, which is a URI [RFC3986] that uniquely    identifies the relation type. |  | [15687:15854] sha256 98c72672c1d4 |
| proposed | Claim | None None | Concept | Relation types are registered using the Specification Required policy    (see Section 4.6 of [RFC8126]), which implies review and approval by    a designated expert. |  | [14567:14732] sha256 715e4f59fc15 |
| proposed | Claim | None None | Concept | Relation types are registered using the Specification Required policy    (see Section 4.6 of [RFC8126]), which implies review and approval by    a designated expert. |  | [14567:14732] sha256 715e4f59fc15 |
| proposed | Claim | None None | Concept | Target attributes are a list of key/value pairs that describe the    link or its target; for example, a media type hint. |  | [16867:16987] sha256 5930b15d90b3 |
| proposed | Claim | None None | Definition | Target attributes are a list of key/value pairs that describe the    link or its target; for example, a media type hint. |  | [16867:16987] sha256 5930b15d90b3 |
| proposed | Claim | None None | Definition | Applications that don't wish to register a relation type can use an    extension relation type, which is a URI [RFC3986] that uniquely    identifies the relation type. |  | [15687:15854] sha256 98c72672c1d4 |
| proposed | Claim | None None | Claim | Relation types are registered using the Specification Required policy    (see Section 4.6 of [RFC8126]), which implies review and approval by    a designated expert. |  | [14567:14732] sha256 715e4f59fc15 |
| proposed | Claim | None None | Claim | Although the URI can point to a    resource that contains a definition of the semantics of the relation    type, clients SHOULD NOT automatically access that resource to avoid    overburdening its server. |  | [15856:16060] sha256 f97561a9eee4 |
| proposed | Claim | None None | Practice | Because of this, all-lowercase URIs SHOULD be used for extension    relations. |  | [16408:16486] sha256 d3131b1a6f53 |
| proposed | Claim | None None | Concept | The Link header field provides a means for serialising one or more    links into HTTP headers. |  | [18096:18190] sha256 5cf7f576e7c5 |
| proposed | Claim | None None | Concept | Note that any link-param can be generated with values using either    the token or the quoted-string syntax; therefore, recipients MUST be    able to parse both forms. |  | [18397:18564] sha256 cc8d5dc98ee0 |
| proposed | Claim | None None | Concept | When present, the anchor parameter overrides this with another URI,    such as a fragment of this resource, or a third resource (i.e., when    the anchor value is an absolute URI). |  | [20049:20229] sha256 e654acf10cfc |
| proposed | Claim | None None | Concept | The rel parameter MUST be    present but MUST NOT appear more than once in a given link-value;    occurrences after the first MUST be ignored by parsers. |  | [21330:21483] sha256 b85ac6bc8998 |
| proposed | Claim | None None | Concept | The "hreflang" attribute, when present, is a hint indicating what the    language of the result of dereferencing the link should be. |  | [23306:23438] sha256 b59807875ab2 |
| proposed | Claim | None None | Concept | The "media" attribute, when present, is used to indicate intended    destination medium or media for style information (see    [W3C.REC-html5-20141028], Section 4.2.4). |  | [23819:23987] sha256 4394f79b1ac8 |
| proposed | Claim | None None | Definition | Each link-value conveys one target IRI as a URI-Reference (after    conversion to one, if necessary; see [RFC3987], Section 3.1) inside    angle brackets ("<>"). |  | [19490:19651] sha256 ca49b014e26c |
| proposed | Claim | None None | Concept | The "title" attribute, when present, is used to label the destination    of a link such that it can be used as a human-readable identifier    (e.g., a menu entry) in the language indicated by the Content-    Language header field (if present). |  | [24270:24513] sha256 055fcf258c94 |
| proposed | Claim | None None | Concept | The "title*" link-param can be used to encode this attribute in a    different character set and/or contain language information as per    [RFC8187]. |  | [24649:24798] sha256 e654e1c1bbc5 |
| proposed | Claim | None None | Concept | The "type" attribute, when present, is a hint indicating what the    media type of the result of dereferencing the link should be. |  | [25232:25362] sha256 a29e445eb777 |
| proposed | Claim | None None | Concept | Such target attributes MAY be defined to use the encoding in    [RFC8187] (e.g., "example" and "example*"). |  | [26057:26164] sha256 14d20deddde3 |
| proposed | Claim | None None | Standard | Such target attributes MAY be defined to use the encoding in    [RFC8187] (e.g., "example" and "example*"). |  | [26057:26164] sha256 14d20deddde3 |
| proposed | Claim | None None | Standard | type-name "/" subtype-name ; see Section 4.2 of [RFC6838] |  | [25873:25930] sha256 8d265550f412 |
| proposed | Claim | None None | Concept | Header Field Name: Link    Protocol: http    Status: standard    Reference: RFC 8288 |  | [28670:28754] sha256 2569673f8c1a |
| proposed | Claim | None None | Concept | This specification updates the "Message Headers" registry entry for    "Link" in HTTP [RFC3864] to refer to this document. |  | [28543:28665] sha256 579a55de419c |
| proposed | Claim | None None | Concept | IANA will direct any incoming requests regarding the registry to this    document and, if defined, the processes established by the expert(s);    typically, this will mean referring them to the registry Web page. |  | [29180:29392] sha256 8d3a7122e20d |
| proposed | Claim | None None | Claim | This specification updates the "Message Headers" registry entry for    "Link" in HTTP [RFC3864] to refer to this document. |  | [28543:28665] sha256 579a55de419c |
| proposed | Claim | None None | Claim | IANA will direct any incoming requests regarding the registry to this    document and, if defined, the processes established by the expert(s);    typically, this will mean referring them to the registry Web page. |  | [29180:29392] sha256 8d3a7122e20d |
| proposed | Claim | None None | Claim | Note that the expert(s) is allowed (as per Section 2.1.1.1) to define    additional fields to be collected in the registry. |  | [29397:29520] sha256 2ed99d64af61 |
| proposed | Claim | None None | Claim | Also, all references    to RFC 5988 in that registry have been replaced with references to    this document. |  | [28914:29022] sha256 bd2a66237559 |
| proposed | Claim | None None | Standard | Header Field Name: Link    Protocol: http    Status: standard    Reference: RFC 8288 |  | [28670:28754] sha256 2569673f8c1a |
| proposed | Claim | None None | Concept | The content of the Link header field is not secure, private, or    integrity-guaranteed. |  | [29759:29847] sha256 e33e32962f51 |
| proposed | Claim | None None | Concept | Link applications ought to consider the attack vectors opened by    automatically following, trusting, or otherwise using links gathered    from HTTP header fields. |  | [29983:30147] sha256 01795c0ea94e |
| proposed | Claim | None None | Concept | Use of Transport Layer Security (TLS) with    HTTP [RFC2818] is currently the only end-to-end way to provide these    properties. |  | [29849:29978] sha256 0bbed4a11a9b |
| proposed | Claim | None None | Concept | For example, Link header fields that use the "anchor" parameter to    associate a link's context with another resource cannot be trusted    since they are effectively assertions by a third party that could be    incorrect or malicious. |  | [30152:30387] sha256 c6c644273f14 |
| proposed | Claim | None None | Concept | For example, the Referer header [RFC7231] can    expose information about the application's state (including private    information) in its value. |  | [30673:30819] sha256 657b1d5251aa |
| proposed | Claim | None None | Concept | Likewise, cookies [RFC6265] are another    mechanism that, if used, can become an attack vector. |  | [30821:30917] sha256 14a52eaf151f |
| proposed | Claim | None None | Claim | The content of the Link header field is not secure, private, or    integrity-guaranteed. |  | [29759:29847] sha256 e33e32962f51 |
| proposed | Claim | None None | Claim | Use of Transport Layer Security (TLS) with    HTTP [RFC2818] is currently the only end-to-end way to provide these    properties. |  | [29849:29978] sha256 0bbed4a11a9b |
| proposed | Claim | None None | Claim | Link applications ought to consider the attack vectors opened by    automatically following, trusting, or otherwise using links gathered    from HTTP header fields. |  | [29983:30147] sha256 01795c0ea94e |
| proposed | Claim | None None | Claim | For example, Link header fields that use the "anchor" parameter to    associate a link's context with another resource cannot be trusted    since they are effectively assertions by a third party that could be    incorrect or malicious. |  | [30152:30387] sha256 c6c644273f14 |
| proposed | Claim | None None | Claim | For example, the Referer header [RFC7231] can    expose information about the application's state (including private    information) in its value. |  | [30673:30819] sha256 657b1d5251aa |
| proposed | Claim | None None | Claim | Likewise, cookies [RFC6265] are another    mechanism that, if used, can become an attack vector. |  | [30821:30917] sha256 14a52eaf151f |
| proposed | Claim | None None | Concept | Link targets may need to be converted to URIs in order to express    them in serialisations that do not support IRIs. |  | [31528:31645] sha256 6fd170330a38 |
| proposed | Claim | None None | Concept | Similarly, the anchor parameter of the Link header field does not    support IRIs; therefore, IRIs must be converted to URIs before    inclusion there. |  | [31696:31847] sha256 0cb0578fcafc |
| proposed | Claim | None None | Concept | This includes the    Link HTTP header field. |  | [31647:31691] sha256 a14a030e8e2d |
| proposed | Claim | None None | Concept | Similarly, the anchor parameter of the Link header field does not    support IRIs; therefore, IRIs must be converted to URIs before    inclusion there. |  | [31696:31847] sha256 0cb0578fcafc |
| proposed | Claim | None None | Concept | Relation types are defined as URIs, not IRIs, to aid in their    comparison. |  | [31852:31928] sha256 191cff6cf938 |
| proposed | Claim | None None | Concept | Note that registered Relation Names are required to be lowercase    ASCII letters. |  | [31998:32080] sha256 8fe7d61a8133 |
| proposed | Claim | None None | Claim | Link targets may need to be converted to URIs in order to express    them in serialisations that do not support IRIs. |  | [31528:31645] sha256 6fd170330a38 |
| proposed | Claim | None None | Claim | Similarly, the anchor parameter of the Link header field does not    support IRIs; therefore, IRIs must be converted to URIs before    inclusion there. |  | [31696:31847] sha256 0cb0578fcafc |
| proposed | Claim | None None | Claim | Relation types are defined as URIs, not IRIs, to aid in their    comparison. |  | [31852:31928] sha256 191cff6cf938 |
| proposed | Claim | None None | Claim | Note that registered Relation Names are required to be lowercase    ASCII letters. |  | [31998:32080] sha256 8fe7d61a8133 |
| proposed | Claim | None None | Concept | Note that registered Relation Names are required to be lowercase    ASCII letters. |  | [31998:32080] sha256 8fe7d61a8133 |
| proposed | Claim | None None | Concept | HTML motivated the original syntax of the Link header field, and many    of the design decisions in this document are driven by a desire to    stay compatible with it. |  | [37031:37198] sha256 b54200dc9b12 |
| proposed | Claim | None None | Concept | In HTML, the link element can be mapped to links as specified here by    using the "href" attribute for the target URI, and "rel" to convey    the relation type, as in the Link header field. |  | [37203:37393] sha256 9c5bdb1bf8c8 |
| proposed | Claim | None None | Concept | That document links to the Microformats Wiki as a registry;    over time, the IANA registry ought to mirror its contents and,    ideally, eventually replace it (although that depends on the HTML    community). |  | [37700:37909] sha256 ffafd2a04e1b |
| proposed | Claim | None None | Concept | That document links to the Microformats Wiki as a registry;    over time, the IANA registry ought to mirror its contents and,    ideally, eventually replace it (although that depends on the HTML    community). |  | [37700:37909] sha256 ffafd2a04e1b |
| proposed | Claim | None None | Concept | Atom [RFC4287] is a link serialisation that conveys links in the    atom:link element, with the "href" attribute indicating the link    target and the "rel" attribute containing the relation type. |  | [38636:38832] sha256 a9ae96f2e71e |
| proposed | Claim | None None | Concept | Furthermore, link relation types are always compared in a case-    sensitive fashion; therefore, registered link relation types SHOULD    be converted to their registered form (usually, lowercase) when    serialised in an Atom document. |  | [39671:39907] sha256 7923f65a2edd |
| proposed | Claim | None None | Concept | This prefix is specific to the Atom serialisation. |  | [39616:39666] sha256 94757442995d |
| proposed | Claim | None None | Claim | HTML motivated the original syntax of the Link header field, and many    of the design decisions in this document are driven by a desire to    stay compatible with it. |  | [37031:37198] sha256 b54200dc9b12 |
| proposed | Claim | None None | Claim | That document links to the Microformats Wiki as a registry;    over time, the IANA registry ought to mirror its contents and,    ideally, eventually replace it (although that depends on the HTML    community). |  | [37700:37909] sha256 ffafd2a04e1b |
| proposed | Claim | None None | Claim | This prefix is specific to the Atom serialisation. |  | [39616:39666] sha256 94757442995d |
| proposed | Claim | None None | Claim | Atom defines extension relation types in terms of IRIs. |  | [39309:39364] sha256 866823d8bd1b |
| proposed | Claim | None None | Standard | Section 4.8 of HTML5 [W3C.REC-html5-20141028] defines modern HTML    links. |  | [37623:37698] sha256 2148282b5899 |
| proposed | Claim | None None | Standard | Atom [RFC4287] is a link serialisation that conveys links in the    atom:link element, with the "href" attribute indicating the link    target and the "rel" attribute containing the relation type. |  | [38636:38832] sha256 a9ae96f2e71e |
| proposed | Claim | None None | Practice | Furthermore, link relation types are always compared in a case-    sensitive fashion; therefore, registered link relation types SHOULD    be converted to their registered form (usually, lowercase) when    serialised in an Atom document. |  | [39671:39907] sha256 7923f65a2edd |
| proposed | Claim | None None | Concept | This algorithm can be used to parse the Link header fields that a    HTTP header set contains. |  | [40965:41059] sha256 103511116bc8 |
| proposed | Claim | None None | Concept | This algorithm can be used to parse the Link header fields that a    HTTP header set contains. |  | [40965:41059] sha256 103511116bc8 |
| proposed | Claim | None None | Concept | Given a header_set of (string field_name,    string field_value) pairs, assuming ASCII encoding, it returns a list    of link objects. |  | [41061:41195] sha256 e57ce12fd4e8 |
| proposed | Claim | None None | Concept | 1.  Let value_links be the result of Parsing a Link Field Value |  | [41576:41639] sha256 5138fdef4477 |
| proposed | Claim | None None | Concept | This algorithm parses zero or more comma-separated link-values from a    Link header field. |  | [41799:41890] sha256 a80cae574369 |
| proposed | Claim | None None | Concept | Given a string field_value, assuming ASCII    encoding, it returns a list of link objects. |  | [41892:41982] sha256 96d1528c46e1 |
| proposed | Claim | None None | Standard | [RFC3986], Section 5.2) target_string. |  | [42701:42739] sha256 362ba4977adc |
| proposed | Claim | None None | Standard | [RFC3986], Section 5.2) target_string. |  | [42701:42739] sha256 362ba4977adc |
| proposed | Claim | None None | Concept | link_parameters whose first item matches the string             "anchor". |  | [43225:43298] sha256 e98a5e85b249 |
| proposed | Claim | None None | Concept | 11.  Let context_string be the second item of the first tuple of |  | [43148:43212] sha256 7b4b04fc0463 |
| proposed | Claim | None None | Definition | 11.  Let context_string be the second item of the first tuple of |  | [43148:43212] sha256 7b4b04fc0463 |
| proposed | Claim | None None | Standard | If it is not present, context_string is the URL             of the representation carrying the Link header [RFC7231],             Section 3.1.4.1, serialised as a URI. |  | [43300:43467] sha256 d78ecbeb39f3 |
| proposed | Claim | None None | Concept | Where the URL is             anonymous, context_string is null. |  | [43469:43532] sha256 23cc945e9353 |
| proposed | Claim | None None | Concept | If it is not present, context_string is the URL             of the representation carrying the Link header [RFC7231],             Section 3.1.4.1, serialised as a URI. |  | [43300:43467] sha256 d78ecbeb39f3 |
| proposed | Claim | None None | Concept | link_parameters whose first item matches the string             "anchor". |  | [43225:43298] sha256 e98a5e85b249 |
| proposed | Claim | None None | Concept | internationalised form of a parameter named                 base_param_name for any reason (including, but not                 limited to, it being prohibited by the parameter's                 specification), remove all tuples from link_parameters                 whose first member is star_param_name, and skip to the                 next star_param_name. |  | [44942:45299] sha256 b04d3a61af2c |
| proposed | Claim | None None | Concept | internationalised form of a parameter named                 base_param_name for any reason (including, but not                 limited to, it being prohibited by the parameter's                 specification), remove all tuples from link_parameters                 whose first member is star_param_name, and skip to the                 next star_param_name. |  | [44942:45299] sha256 b04d3a61af2c |
| proposed | Claim | None None | Claim | This algorithm parses the parameters from a header field value. |  | [45941:46004] sha256 30a8ec254c25 |
| proposed | Claim | None None | Claim | input is modified to remove the parsed parameters. |  | [46138:46188] sha256 db9e72c445fe |
| proposed | Claim | None None | Concept | 1.  Let parameters be an empty list. |  | [46193:46229] sha256 e54bd9fcb3cf |
| proposed | Claim | None None | Concept | 5.   Consume up to but not including the first BWS, "=", ";", or |  | [46610:46674] sha256 a2dfa2f43fc8 |
| proposed | Claim | None None | Concept | "," character, or up to the end of input, and let the result             be parameter_name. |  | [46687:46778] sha256 120897be840a |
| proposed | Claim | None None | Concept | 6.   Consume any leading BWS. |  | [46786:46815] sha256 10f2e0c78793 |
| proposed | Claim | None None | Concept | ("*"), decode parameter_value according to [RFC8187]. |  | [47446:47499] sha256 c3a257615fdb |
| proposed | Claim | None None | Standard | ("*"), decode parameter_value according to [RFC8187]. |  | [47446:47499] sha256 c3a257615fdb |
| proposed | Claim | None None | Concept | 1.  Let parameter_value be an empty string. |  | [47630:47673] sha256 96ed7f543dff |
| proposed | Claim | None None | Concept | 9.   Case-normalise parameter_name to lowercase. |  | [47681:47729] sha256 baa536bede11 |
| proposed | Claim | None None | Concept | 11.  Consume any leading OWS. |  | [47805:47834] sha256 536528319cac |
| proposed | Claim | None None | Standard | ("*"), decode parameter_value according to [RFC8187]. |  | [47446:47499] sha256 c3a257615fdb |
| proposed | Claim | None None | Concept | This algorithm parses a quoted string, as per [RFC7230],    Section 3.2.6. |  | [47989:48063] sha256 f4847e4dd890 |
| proposed | Claim | None None | Standard | This algorithm parses a quoted string, as per [RFC7230],    Section 3.2.6. |  | [47989:48063] sha256 f4847e4dd890 |
| proposed | Claim | None None | Concept | o  Terminology was changed from "target IRI" and "context IRI" to       "link target" and "link context", respectively. |  | [49387:49506] sha256 4a8e634b3c27 |
| proposed | Claim | None None | Concept | o  Removed misleading statement that the Link header field is       semantically equivalent to HTML and Atom links. |  | [49596:49711] sha256 8f7ee32524ac |
| proposed | Claim | None None | Concept | o  More carefully defined and used "link serialisations" and "link       applications."    o  Clarified the cardinality of target attributes (generically and       for "type"). |  | [49715:49891] sha256 260df6040b21 |
| proposed | Claim | None None | Claim | o  Corrected the default link context for the Link header field, to       be dependent upon the identity of the representation (as per |  | [49895:50029] sha256 c99badfd6c9a |
| proposed | Claim | None None | Claim | o  Parameters on the HTTP header can now be valueless. |  | [50400:50454] sha256 788df07783ec |
| proposed | Claim | None None | Claim | o  The ABNF has been updated to be compatible with [RFC7230]. |  | [50205:50266] sha256 b8448b9ca6c3 |
| proposed | Claim | None None | about | This specification does not place restrictions on the cardinality of    links; there can be multiple links to and from a particular target    and multiple links of the same or different types between a given    context and target. |  | [8327:8557] sha256 587263dba661 |
| proposed | Claim | None None | about | Registered relation type names MUST conform to the reg-rel-type rule    (see Section 3.3) and MUST be compared character by character in a    case-insensitive fashion. |  | [11467:11634] sha256 c7db63b4fd63 |
| proposed | Claim | None None | about | Relation types SHOULD NOT infer any additional semantics based upon    the presence or absence of another link relation type, or its own    cardinality of occurrence. |  | [10855:11021] sha256 e80263685406 |
| proposed | Claim | None None | about | Relation types are registered using the Specification Required policy    (see Section 4.6 of [RFC8126]), which implies review and approval by    a designated expert. |  | [14567:14732] sha256 715e4f59fc15 |
| proposed | Claim | None None | about | This specification updates the "Message Headers" registry entry for    "Link" in HTTP [RFC3864] to refer to this document. |  | [28543:28665] sha256 579a55de419c |
| proposed | Claim | None None | about | This specification updates the "Message Headers" registry entry for    "Link" in HTTP [RFC3864] to refer to this document. |  | [28543:28665] sha256 579a55de419c |
| proposed | Claim | None None | about | IANA will direct any incoming requests regarding the registry to this    document and, if defined, the processes established by the expert(s);    typically, this will mean referring them to the registry Web page. |  | [29180:29392] sha256 8d3a7122e20d |
| proposed | Claim | None None | about | The content of the Link header field is not secure, private, or    integrity-guaranteed. |  | [29759:29847] sha256 e33e32962f51 |
| proposed | Claim | None None | about | Use of Transport Layer Security (TLS) with    HTTP [RFC2818] is currently the only end-to-end way to provide these    properties. |  | [29849:29978] sha256 0bbed4a11a9b |
| proposed | Claim | None None | about | Link applications ought to consider the attack vectors opened by    automatically following, trusting, or otherwise using links gathered    from HTTP header fields. |  | [29983:30147] sha256 01795c0ea94e |
| proposed | Claim | None None | about | For example, Link header fields that use the "anchor" parameter to    associate a link's context with another resource cannot be trusted    since they are effectively assertions by a third party that could be    incorrect or malicious. |  | [30152:30387] sha256 c6c644273f14 |
| proposed | Claim | None None | about | For example, the Referer header [RFC7231] can    expose information about the application's state (including private    information) in its value. |  | [30673:30819] sha256 657b1d5251aa |
| proposed | Claim | None None | about | Likewise, cookies [RFC6265] are another    mechanism that, if used, can become an attack vector. |  | [30821:30917] sha256 14a52eaf151f |
| proposed | Claim | None None | about | Link targets may need to be converted to URIs in order to express    them in serialisations that do not support IRIs. |  | [31528:31645] sha256 6fd170330a38 |
| proposed | Claim | None None | about | This includes the    Link HTTP header field. |  | [31647:31691] sha256 a14a030e8e2d |
| proposed | Claim | None None | about | Similarly, the anchor parameter of the Link header field does not    support IRIs; therefore, IRIs must be converted to URIs before    inclusion there. |  | [31696:31847] sha256 0cb0578fcafc |
| proposed | Claim | None None | about | Similarly, the anchor parameter of the Link header field does not    support IRIs; therefore, IRIs must be converted to URIs before    inclusion there. |  | [31696:31847] sha256 0cb0578fcafc |
| proposed | Claim | None None | about | Relation types are defined as URIs, not IRIs, to aid in their    comparison. |  | [31852:31928] sha256 191cff6cf938 |
| proposed | Claim | None None | about | Note that registered Relation Names are required to be lowercase    ASCII letters. |  | [31998:32080] sha256 8fe7d61a8133 |
| proposed | Claim | None None | about | HTML motivated the original syntax of the Link header field, and many    of the design decisions in this document are driven by a desire to    stay compatible with it. |  | [37031:37198] sha256 b54200dc9b12 |
| proposed | Claim | None None | about | HTML motivated the original syntax of the Link header field, and many    of the design decisions in this document are driven by a desire to    stay compatible with it. |  | [37031:37198] sha256 b54200dc9b12 |
| proposed | Claim | None None | about | That document links to the Microformats Wiki as a registry;    over time, the IANA registry ought to mirror its contents and,    ideally, eventually replace it (although that depends on the HTML    community). |  | [37700:37909] sha256 ffafd2a04e1b |
| proposed | Claim | None None | about | This prefix is specific to the Atom serialisation. |  | [39616:39666] sha256 94757442995d |
| proposed | Claim | None None | about | Atom defines extension relation types in terms of IRIs. |  | [39309:39364] sha256 866823d8bd1b |
| proposed | Claim | None None | about | This algorithm parses the parameters from a header field value. |  | [45941:46004] sha256 30a8ec254c25 |
| proposed | Claim | None None | about | This algorithm parses the parameters from a header field value. |  | [45941:46004] sha256 30a8ec254c25 |
| proposed | Claim | None None | about | o  Corrected the default link context for the Link header field, to       be dependent upon the identity of the representation (as per |  | [49895:50029] sha256 c99badfd6c9a |
| ungrounded | | None None |  | ungrounded |  | |
| ungrounded | | None None |  | ungrounded |  | |
| ungrounded | | None None |  | ungrounded |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |
| kept_out | | None None |  | kept_out |  | |

