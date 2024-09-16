class Block:
    def __init__(self, block_data):
        self.id = block_data.get("Id", "")
        self.block_type = block_data.get("BlockType", "")
        self.text = block_data.get("Text", "")  # Keep original text as-is
        self.normalized_text = self.text.lower()  # Normalize text for comparison
        self.geometry = block_data.get("Geometry", {})
        # self.relationships = block_data.get("Relationships", [])

    def to_dict(self):
        # Create a copy of the geometry and remove the Polygon key if it exists
        filtered_geometry = {k: v for k, v in self.geometry.items() if k != "Polygon"}

        return {
            "Id": self.id,
            "BlockType": self.block_type,
            "Text": self.text,
            "normalized_text": self.normalized_text,
            "Geometry": filtered_geometry,
            # "relationships": self.relationships,
        }

    def __str__(self) -> str:
        return self.text

    def get_bounding_box(self, image_width, image_height):
        bounding_box = self.geometry.get("BoundingBox", {})
        # image_width = 800  # Example image width (replace with actual image width)
        # image_height = 600  # Example image height (replace with actual image height)

        left = bounding_box.get("Left", 0.0) * image_width
        top = bounding_box.get("Top", 0.0) * image_height
        width = bounding_box.get("Width", 0.0) * image_width
        height = bounding_box.get("Height", 0.0) * image_height

        return left, top, width, height
