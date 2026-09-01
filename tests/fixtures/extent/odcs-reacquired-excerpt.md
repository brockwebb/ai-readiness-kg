# odcs-open-data-contract-standard

> Extent-corrected acquisition. ODCS v3.1.0, released 2025-12-08 (GitHub release tag).

> Extent note: Full specification: every markdown source file under docs/ at tag v3.1.0. Deliberately excluded: docs/examples/ (illustrative YAML instances, not normative text) and docs/img/ (figures). The superseded capture was the rendered site landing page, 2,630 visible characters of navigation.

> Sections: 12. Each section below names the source it came from.

---

# README

Source: https://github.com/bitol-io/open-data-contract-standard/blob/v3.1.0/docs/README.md

---
title: "Definition: Open Data Contract Standard (ODCS)"
description: "Details of the Open Data Contract Standard (ODCS). Includes fundamentals, datasets, schemas, data quality, pricing, stakeholders, roles, service-level agreements and other properties."
image: "https://raw.githubusercontent.com/bitol-io/artwork/main/horizontal/color/Bitol_Logo_color.svg"
---

# Open Data Contract Standard

## Executive Summary

This document describes the keys and values expected in a YAML data contract, per the **Open Data Contract Standard**. The standard is divided in multiple sections. Each section starts with at least an example, followed by the definition of each field/key. Since v3.1.0, each section has its own page for easier readability.

For more details, see the sections below:

1. [Fundamentals](./fundamentals.md)
2. [Schema](./schema.md)
3. [References](./references.md)
4. [Data Quality](./data-quality.md)
5. [Support & Communication Channels](./support-communication-channels.md)
6. [Pricing](./pricing.md)
7. [Team](./team.md)
8. [Roles](./roles.md)
9. [Service-Level Agreement](./service-level-agreement.md)
10. [Infrastructures & Servers](./infrastructure-servers.md)
11. [Custom & Other Properties](./custom-other-properties.md)

## Notes

* The sections above contain example values. We carefully reviewed the consistency of those values, but we cannot guarantee that there are no errors. If you spot one, please raise an [issue](https://github.com/AIDAUserGroup/open-data-contract-standard/issues).
* Some fields have a `null` value: even if it is equivalent to not having the field in the contract, we wanted to have the field for illustration purposes.
* The contract should be **platform agnostic**. If you think this is not the case, please raise an [issue](https://github.com/AIDAUserGroup/open-data-contract-standard/issues).
* The provided JSON schemas are companions to the standards (ODCS or ODPS), it means that they do not define the standards and may include bugs. In case of conflict between the standard and the JSON Schema, the standard takes precedence.

## Full example

[Check full example here.](examples/all/full-example.odcs.yaml)

All trademarks are the property of their respective owners.

---

# custom-other-properties

Source: https://github.com/bitol-io/open-data-contract-standard/blob/v3.1.0/docs/custom-other-properties.md

---
title: "Custom & Other Properties"
description: "This section covers custom properties you may find in a data contract."
---

# Custom & Other Properties

This section covers other properties you may find in a data contract.

[Back to TOC](README.md)

## Custom Properties

This section covers custom properties you can use to add non-standard properties. This block is available in many
sections.

### Example

```YAML
customProperties:
  - id: rfc_ruleset_name
    property: refRulesetName
    value: gcsc.ruleset.name
  - id: some_property_name
    property: somePropertyName
    value: property.value
  - id: data_proc_cluster_name
    property: dataprocClusterName # Used for specific applications
    value: [ cluster name ]
    description: Cluster name for specific applications
```

### Definitions

| Key                          | UX label          | Required | Description                                                                                                                                                                                |
|------------------------------|-------------------|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| customProperties             | Custom Properties | No       | A list of key/value pairs for custom properties. Initially created to support the REF ruleset property.                                                                                    |
| customProperties.id          | ID                | No       | A unique identifier for the element used to create stable, refactor-safe references. Recommended for elements that will be referenced. See [References](./references.md) for more details. |
| customProperties.property    | Property          | No       | The name of the key. Names should be in camel case–the same as if they were permanent properties in the contract.                                                                          |
| customProperties.value       | Value             | No       | The value of the key. It can be an array.                                                                                                                                                  |
| customProperties.description | Description       | No       | Description for humans.                                                                                                                                                                    |

## Authoritative Definitions

Authoritative Definitions are an essential part of the contract. They allow to delegate the definition to a third party
system like an enterprise catalog, repository, etc. The structure describing "Authoritative Definitions" is shared
between all Bitol standards. This block is available in many sections.

### Example

```yaml
    authoritativeDefinitions:
      - url: https://catalog.data.gov/dataset/air-quality
        type: businessDefinition
        description: Business definition for the dataset.
      - url: https://www.youtube.com/watch?v=Iq6SxdsIHHE
        type: videoTutorial
        description: Discover what a data contract is.
      - url: https://github.com/bitol-io/open-data-contract-standard/blob/main/docs/examples/all/full-example.odcs.yaml
        type: canonicalUrl
        description: Data contract's latest version.
```

### Definitions

| Key                                  | UX label          | Required | Description                                                                                                                                                                                                                                                                            |
|--------------------------------------|-------------------|----------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| authoritativeDefinitions             | Link              | No       | A list of type/link pairs for authoritative definitions.                                                                                                                                                                                                                               |
| authoritativeDefinitions.id          | ID                | No       | A unique identifier for the element used to create stable, refactor-safe references. Recommended for elements that will be referenced. See [References](./references.md) for more details.                                                                                             |
| authoritativeDefinitions.type        | Definition type   | Yes      | Type of definition for authority. Recommended values are: `businessDefinition`, `transformationImplementation`, `videoTutorial`, `tutorial`, and `implementation`. At the root level, a type can also be `canonicalUrl` to indicate a reference to the data contract's latest version. |
| authoritativeDefinitions.url         | URL to definition | Yes      | URL to the authority.                                                                                                                                                                                                                                                                  |
| authoritativeDefinitions.description | Description       | No       | Optional description.                                                                                                                                                                                                                                                                  |

## Other Properties

This section covers other properties you may find in a data contract.

### Example

```YAML
contractCreatedTs: 2024-09-17T11:58:08Z
```

### Other properties definition

| Key               | UX label             | Required | Description                                                             |
|-------------------|----------------------|----------|-------------------------------------------------------------------------|
| contractCreatedTs | Contract Created UTC | No       | Timestamp in UTC of when the data contract was created, using ISO 8601. |

[Back to TOC](README.md)

---

# data-quality

Source: https://github.com/bitol-io/open-data-contract-standard/blob/v3.1.0/docs/data-quality.md
