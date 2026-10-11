#!/usr/bin/env python3
import importlib.util, json, tempfile, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
assembler=module("af_assembler",ROOT/"scripts/assemble_aesthetic_input.py")
arouter=module("af_arouter",ROOT/"scripts/route_aesthetic_result.py")
crouter=module("af_crouter",ROOT/"scripts/route_consumer_result.py")
version=json.loads((ROOT/"assets/config/version.json").read_text(encoding="utf-8"))
protected={k:{"value":k} for k in ["product_identity","product_quantity","brand_and_logo","price_and_unit","promotion_and_period","selling_points","cta","legal_text"]}
candidate={"schema_version":"A-D-2.0","request_id":"r1","poster_image":"poster.png","protected_content":protected,"loop_state":{"version_id":"v1"}}
details={"dimension_scores":{"composition":16,"hierarchy":16,"color":12,"typography":16,"consistency":12,"finish":8},"critical_issues":[],"request_id":"r1","version_id":"v1","poster_image":"poster.png","context_hash":"h1"}
aesthetic={"agent_name":"aesthetic_agent","score":80,"pass":True,"problem_list":[],"modify_suggestion":[],"protected_content":protected,"meta":{"judge_dimensions":[],"confidence":.8}}

class TestAF(unittest.TestCase):
    def test_assembler_has_no_consumer_result(self):
        value=assembler.assemble(candidate);self.assertEqual(set(value),{"schema_version","evaluation_phase","candidate"})
    def test_aesthetic_pass_invokes_consumer(self):
        workflow=assembler.assemble(candidate);value=arouter.route(aesthetic,details,workflow,version,0);self.assertEqual(value["action"],"invoke_consumer_agent")
    def test_consumer_pass_maps_to_final_gate(self):
        consumer={"schema_version":"A-D-2.0","agent_name":"consumer_agent","request_id":"r1","version_id":"v1","score":80,"dimension_scores":{k:16 for k in crouter.CDIMS},"locked_dimensions":sorted(crouter.CDIMS),"regressed_dimensions":[],"hard_fail":False,"pass":True,"next_route":"aesthetic_agent","protected_content":protected}
        value=crouter.route(consumer,aesthetic,details,version,0);self.assertEqual(value["action"],"invoke_final_quality_gate")
    def test_consumer_failure_freezes_aesthetic(self):
        consumer={"schema_version":"A-D-2.0","agent_name":"consumer_agent","request_id":"r1","version_id":"v1","score":70,"dimension_scores":{k:(10 if k=="purchase_drive" else 16) for k in crouter.CDIMS},"locked_dimensions":[],"regressed_dimensions":[],"hard_fail":False,"pass":False,"next_route":"poster_generation_skill","protected_content":protected,"modify_suggestion":["local"]}
        value=crouter.route(consumer,aesthetic,details,version,0);contract=value["generation_edit_contract"];self.assertEqual(set(contract["locked_aesthetic_dimensions"]),set(arouter.MINIMUMS));self.assertEqual(contract["editable_consumer_dimensions"],["purchase_drive"])

if __name__=="__main__": unittest.main()
