<?xml version="1.0" encoding="UTF-8"?>
<schema xmlns="http://purl.oclc.org/dsdl/schematron"
        xmlns:ubl="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
        xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
        queryBinding="xslt">
  <title>Minimal XRechnung-like checks for test harness</title>
  <pattern id="buyer-reference-required">
    <rule context="ubl:Invoice">
      <assert id="BR-DE-001" test="normalize-space(cbc:BuyerReference) != ''">BR-DE-001 BuyerReference is required.</assert>
      <assert id="EN16931-BR-CO-10" test="normalize-space(cbc:DocumentCurrencyCode) != ''">EN16931-BR-CO-10 DocumentCurrencyCode is required.</assert>
    </rule>
  </pattern>
</schema>
